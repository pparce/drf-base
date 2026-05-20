from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from src.apps.user.models import User


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="securepassword123",
        )

    def test_user_str(self):
        self.assertEqual(str(self.user), "test@example.com")

    def test_password_is_hashed(self):
        self.assertNotEqual(self.user.password, "securepassword123")
        self.assertTrue(self.user.check_password("securepassword123"))

    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            password="adminpassword123",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class AuthRegisterTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        response = self.client.post("/api/auth/register/", {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "securepassword123",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertNotIn("password", response.data.get("user", {}))

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email="existing@example.com",
            first_name="Existing",
            last_name="User",
            password="securepassword123",
        )
        response = self.client.post("/api/auth/register/", {
            "email": "existing@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "securepassword123",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_register_short_password(self):
        response = self.client.post("/api/auth/register/", {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "short",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="login@example.com",
            first_name="Login",
            last_name="User",
            password="securepassword123",
        )

    def test_login_success(self):
        response = self.client.post("/api/auth/login/", {
            "username": "login@example.com",
            "password": "securepassword123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertNotIn("password", response.data.get("user", {}))

    def test_login_wrong_password(self):
        response = self.client.post("/api/auth/login/", {
            "username": "login@example.com",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="changepw@example.com",
            first_name="Change",
            last_name="Password",
            password="oldpassword123",
        )
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        response = self.client.post("/api/users/change_password/", {
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword456"))

    def test_change_password_wrong_current(self):
        response = self.client.post("/api/users/change_password/", {
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_short_new(self):
        response = self.client.post("/api/users/change_password/", {
            "current_password": "oldpassword123",
            "new_password": "short",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RestorePasswordTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="restore@example.com",
            first_name="Restore",
            last_name="User",
            password="originalpassword123",
        )

    def test_restore_password_success(self):
        self.user.restore_code = "123456"
        self.user.save()
        response = self.client.post("/api/auth/restore_password/", {
            "email": "restore@example.com",
            "code": "123456",
            "new_password": "newpassword456",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword456"))
        self.assertIsNone(self.user.restore_code)

    def test_restore_password_wrong_code(self):
        self.user.restore_code = "123456"
        self.user.save()
        response = self.client.post("/api/auth/restore_password/", {
            "email": "restore@example.com",
            "code": "000000",
            "new_password": "newpassword456",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HealthCheckTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertIn("database", response.data)
