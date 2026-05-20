import logging

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

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
