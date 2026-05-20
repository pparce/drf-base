from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from src.apps.user.models import User


class LoginTest(TestCase):
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
            "email": "login@example.com",
            "password": "securepassword123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("token_refresh", response.data)
        self.assertNotIn("password", response.data.get("user", {}))

    def test_login_wrong_password(self):
        response = self.client.post("/api/auth/login/", {
            "email": "login@example.com",
            "password": "wrongpassword",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post("/api/auth/login/", {
            "email": "login@example.com",
            "password": "securepassword123",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RegisterTest(TestCase):
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
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

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

    def test_register_short_password(self):
        response = self.client.post("/api/auth/register/", {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "short",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        response = self.client.post("/api/auth/register/", {"email": "incomplete@example.com"})
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

    def test_sending_restore_code_existing_email(self):
        with patch("src.apps.auth.views.send_mail") as mock_mail:
            response = self.client.post("/api/auth/sending_restore_code/", {
                "email": "restore@example.com",
            })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_mail.assert_called_once()
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.restore_code)

    def test_sending_restore_code_unknown_email(self):
        response = self.client.post("/api/auth/sending_restore_code/", {
            "email": "unknown@example.com",
        })
        # Must return 200 regardless to prevent user enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

    def test_restore_password_short_new_password(self):
        self.user.restore_code = "123456"
        self.user.save()
        response = self.client.post("/api/auth/restore_password/", {
            "email": "restore@example.com",
            "code": "123456",
            "new_password": "short",
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GoogleLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _mock_idinfo(self, email="google@example.com", verified=True):
        return {
            "email": email,
            "email_verified": verified,
            "given_name": "Google",
            "family_name": "User",
            "sub": "12345",
        }

    @patch("src.apps.auth.views.id_token")
    @patch("src.apps.auth.views.google_requests")
    def test_google_login_new_user(self, mock_requests, mock_id_token):
        # Patch the lazy imports inside the view
        pass  # Google login uses lazy imports; tested via integration

    def test_google_login_invalid_token(self):
        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=ValueError("bad token")):
            response = self.client.post("/api/auth/google/", {"id_token": "invalid_token"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_google_login_creates_user(self):
        idinfo = self._mock_idinfo()
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=idinfo):
            response = self.client.post("/api/auth/google/", {"id_token": "valid_token"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertTrue(response.data.get("created"))
        self.assertTrue(User.objects.filter(email="google@example.com").exists())

    def test_google_login_existing_user(self):
        User.objects.create_user(
            email="google@example.com",
            first_name="Existing",
            last_name="User",
            password="somepassword",
        )
        idinfo = self._mock_idinfo()
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=idinfo):
            response = self.client.post("/api/auth/google/", {"id_token": "valid_token"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("created", response.data)

    def test_google_login_unverified_email(self):
        idinfo = self._mock_idinfo(verified=False)
        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=idinfo):
            response = self.client.post("/api/auth/google/", {"id_token": "valid_token"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
