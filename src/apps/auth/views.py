import logging

from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from src.api.throttles import AuthRateThrottle
from src.api.utils import generate_code
from src.apps.user.models import User
from src.apps.user.serializers import UserSerializer
from src.apps.auth.serializers import (
    LoginSerializer,
    RegisterSerializer,
    SendRestoreCodeSerializer,
    RestorePasswordSerializer,
    GoogleLoginSerializer,
)
from src.shared.tasks.email_tasks import send_password_reset_email, send_welcome_email

logger = logging.getLogger(__name__)

_RESET_GENERIC_MSG = {"message": "If this email exists, a reset code has been sent"}


def _token_response(user, created=False):
    refresh = RefreshToken.for_user(user)
    data = {
        "token": str(refresh.access_token),
        "token_refresh": str(refresh),
        "user": UserSerializer(user).data,
    }
    if created:
        data["created"] = True
    return data


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @action(detail=False, methods=["post"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data["user"]
        user.restore_code = None
        user.save(update_fields=["restore_code"])
        return Response(_token_response(user))

    @action(detail=False, methods=["post"])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        if User.objects.filter(email=email).exists():
            return Response({"error": "This email is already in use"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = User(
                    email=email,
                    first_name=serializer.validated_data["first_name"],
                    last_name=serializer.validated_data["last_name"],
                    receive_news=serializer.validated_data.get("receive_news", False),
                )
                user.set_password(serializer.validated_data["password"])
                user.save()
        except Exception:
            logger.exception("Error during registration for %s", email)
            return Response({"error": "Registration failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        send_welcome_email.delay(user.email, user.first_name or "User")
        return Response(_token_response(user), status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def sending_restore_code(self, request):
        serializer = SendRestoreCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(_RESET_GENERIC_MSG, status=status.HTTP_200_OK)

        user.restore_code = generate_code()
        user.save(update_fields=["restore_code"])

        send_password_reset_email.delay(email, user.first_name or "User", user.restore_code)
        return Response(_RESET_GENERIC_MSG, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def restore_password(self, request):
        serializer = RestorePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or code"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.restore_code or user.restore_code != code:
            return Response({"error": "Invalid email or code"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.restore_code = None
        user.save()
        return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def google(self, request):
        """
        Exchange a Google ID token (from the client-side Sign-In flow) for JWT tokens.
        Creates a new account on first login.
        """
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_token_value = serializer.validated_data["id_token"]

        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests
            from django.conf import settings

            idinfo = id_token.verify_oauth2_token(
                id_token_value,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError:
            logger.warning("Invalid Google ID token received")
            return Response({"error": "Invalid Google token"}, status=status.HTTP_401_UNAUTHORIZED)

        if not idinfo.get("email_verified"):
            return Response({"error": "Google email is not verified"}, status=status.HTTP_401_UNAUTHORIZED)

        email = idinfo.get("email")
        if not email:
            return Response({"error": "Could not retrieve email from Google token"}, status=status.HTTP_401_UNAUTHORIZED)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": idinfo.get("given_name", ""),
                "last_name": idinfo.get("family_name", ""),
                "is_validate": True,
            },
        )

        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
            send_welcome_email.delay(user.email, user.first_name or "User")

        if not user.is_active:
            return Response({"error": "This account has been disabled"}, status=status.HTTP_403_FORBIDDEN)

        http_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(_token_response(user, created=created), status=http_status)
