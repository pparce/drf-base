from django.test import TestCase
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

    def test_change_password_requires_auth(self):
        unauthenticated = APIClient()
        response = unauthenticated.post("/api/users/change_password/", {
            "current_password": "oldpassword123",
            "new_password": "newpassword456",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserUpdateTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="owner@example.com",
            first_name="Owner",
            last_name="User",
            password="password123",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            first_name="Other",
            last_name="User",
            password="password123",
        )

    def test_user_can_update_own_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/api/users/{self.user.id}/", {"first_name": "Updated"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")

    def test_user_cannot_update_other_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"/api/users/{self.other_user.id}/", {"first_name": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
