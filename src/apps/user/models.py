from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UserManager(BaseUserManager):
    def _create_user(
        self,
        email,
        first_name,
        last_name,
        password,
        is_staff,
        is_superuser,
        **extra_fields
    ):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)  # Cambiado a self._db
        return user

    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        return self._create_user(
            email, first_name, last_name, password, False, False, **extra_fields
        )

    def create_superuser(
        self, email, first_name, last_name, password=None, **extra_fields
    ):
        return self._create_user(
            email, first_name, last_name, password, True, True, **extra_fields
        )

def avatar(instance, filename):
    return "users/{}".format(filename)

class User(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(
        "Email", max_length=255, unique=True
    )  # Cambiado a EmailField
    first_name = models.CharField("Nombre", max_length=255, blank=True, null=True)
    last_name = models.CharField("Apellido", max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)
    is_validate = models.BooleanField(default=False)
    restore_code = models.IntegerField(
        null=True, blank=True
    )  # Añadido blank=True para consistencia
    avatar = models.FileField(upload_to=avatar, null=True, blank=True)
    receive_news = models.BooleanField(default=False)

    objects = UserManager()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def natural_key(self):
        return (self.email,)

    def __str__(self):
        return self.first_name
        # return "Usuario {0}, con Nombre Completo: {1} {2}".format(
        #     self.email, self.first_name, self.last_name
        # )
