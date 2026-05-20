import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from src.api.throttles import AuthRateThrottle
from src.api.utils import generate_code
from src.apps.user.models import User
from src.apps.user.serializers import UserSerializer, UserEditSerializer
from src.shared.views.base_view import BaseModelViewSet

logger = logging.getLogger(__name__)


class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ["admin_create", "create", "list", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request):
        try:
            with transaction.atomic():
                if User.objects.filter(email=request.data.get("email", "")).exists():
                    return Response(
                        {"error": "This email is already in use"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                serializer = self.serializer_class(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception:
            logger.exception("Error creating user")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = User.objects.get(id=kwargs["pk"])
                if not request.user.is_staff and request.user.id != instance.id:
                    return Response(status=status.HTTP_403_FORBIDDEN)
                serializer = UserEditSerializer(data=request.data, instance=instance, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            logger.exception("Error updating user")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def admin_create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                email = request.data.get("email", "")
                existing = User.objects.filter(email=email).first()
                if existing:
                    if existing.is_staff:
                        return Response(
                            {"error": "This email is already in use by a staff member"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    existing.is_staff = True
                    existing.save(update_fields=["is_staff"])
                    return Response(UserSerializer(existing).data)

                serializer = self.serializer_class(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                user.is_staff = True
                user.save(update_fields=["is_staff"])
                return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        except Exception:
            logger.exception("Error in admin_create")
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")

        if not request.user.check_password(current_password):
            return Response(
                {"error": "Current password is incorrect"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not new_password or len(new_password) < 8:
            return Response(
                {"error": "New password must be at least 8 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        return Response({"message": "Password changed successfully"}, status=status.HTTP_200_OK)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]

    @action(detail=False, methods=["post"])
    def login(self, request, *args, **kwargs):
        from rest_framework.authtoken.serializers import AuthTokenSerializer

        serializer = AuthTokenSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        user.restore_code = None
        user.save(update_fields=["restore_code"])
        return Response({
            "token": str(refresh.access_token),
            "token_refresh": str(refresh),
            "user": UserSerializer(user).data,
        })

    @action(detail=False, methods=["post"])
    def sending_restore_code(self, request):
        email = request.data.get("email", "").strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return 200 to prevent user enumeration
            return Response(
                {"message": "If this email exists, a reset code has been sent"},
                status=status.HTTP_200_OK,
            )

        user.restore_code = generate_code()
        user.save(update_fields=["restore_code"])

        try:
            send_mail(
                subject="Password Reset Code",
                message=f"Your password reset code is: {user.restore_code}",
                from_email=settings.EMAIL_HOST_USER or "noreply@example.com",
                recipient_list=[email],
                html_message=(
                    f"<p>Dear {user.first_name or 'User'},</p>"
                    f"<p>Your password reset code is: <strong>{user.restore_code}</strong></p>"
                    f"<p>If you did not request a password reset, please ignore this message.</p>"
                ),
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send password reset email to %s", email)
            return Response(
                {"error": "Failed to send email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "If this email exists, a reset code has been sent"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def restore_password(self, request):
        email = request.data.get("email", "").strip()
        code = str(request.data.get("code", "")).strip()
        new_password = request.data.get("new_password", "")

        if not new_password or len(new_password) < 8:
            return Response(
                {"error": "New password must be at least 8 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
    def register(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                if User.objects.filter(email=request.data.get("email", "")).exists():
                    return Response(
                        {"error": "This email is already in use"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                serializer = UserSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    "token": str(refresh.access_token),
                    "token_refresh": str(refresh),
                    "user": UserSerializer(user).data,
                }, status=status.HTTP_201_CREATED)
        except Exception:
            logger.exception("Error during registration")
            return Response(
                {"error": "Registration failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
