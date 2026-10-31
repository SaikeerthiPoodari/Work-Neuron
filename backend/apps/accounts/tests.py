from django.urls import reverse
import json
from unittest.mock import patch
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthenticationApiTests(APITestCase):
    def test_health_endpoint_reports_database_status(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["status"], "ok")

    def test_registration_creates_worker_without_exposing_password(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "worker@example.com",
                "password": "secure-pass-123",
                "password_confirm": "secure-pass-123",
                "first_name": "Test",
                "role": User.Role.WORKER,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], User.Role.WORKER)
        self.assertNotIn("password", response.data)
        self.assertTrue(User.objects.get(email="worker@example.com").check_password("secure-pass-123"))

    def test_admin_role_cannot_be_self_registered(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "email": "admin@example.com",
                "password": "secure-pass-123",
                "password_confirm": "secure-pass-123",
                "role": User.Role.ADMIN,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="admin@example.com").exists())

    def test_login_returns_jwt_with_role_claim_and_me_requires_authentication(self):
        User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        login = self.client.post(
            reverse("auth-login"),
            {"email": "client@example.com", "password": "secure-pass-123"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data)
        self.assertEqual(login.data["user"]["role"], User.Role.CLIENT)

        unauthenticated = self.client.get(reverse("auth-me"))
        self.assertEqual(unauthenticated.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        authenticated = self.client.get(reverse("auth-me"))
        self.assertEqual(authenticated.status_code, status.HTTP_200_OK)
        self.assertEqual(authenticated.data["email"], "client@example.com")

    def test_login_rejects_wrong_role_entry_point(self):
        User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        response = self.client.post(reverse("auth-login"), {"email": "worker@example.com", "password": "secure-pass-123", "role": User.Role.CLIENT}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Worker Login", str(response.data))

    @patch("apps.accounts.views.send_mail")
    def test_password_reset_request_is_non_enumerating_and_sends_for_active_account(self, send_mail):
        user = User.objects.create_user(email="reset@example.com", password="old-pass-123", role=User.Role.WORKER)
        existing = self.client.post(reverse("auth-password-reset"), {"email": user.email}, format="json")
        missing = self.client.post(reverse("auth-password-reset"), {"email": "missing@example.com"}, format="json")
        self.assertEqual(existing.status_code, status.HTTP_200_OK)
        self.assertEqual(missing.status_code, status.HTTP_200_OK)
        self.assertEqual(existing.data, missing.data)
        send_mail.assert_called_once()

    def test_password_reset_confirm_changes_password_and_invalid_token_is_rejected(self):
        user = User.objects.create_user(email="confirm@example.com", password="old-pass-123", role=User.Role.CLIENT)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = self.client.post(reverse("auth-password-reset-confirm"), {"uid": uid, "token": token, "new_password": "new-pass-456", "new_password_confirm": "new-pass-456"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("new-pass-456"))
        invalid = self.client.post(reverse("auth-password-reset-confirm"), {"uid": uid, "token": token, "new_password": "another-pass-789", "new_password_confirm": "another-pass-789"}, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        user.refresh_from_db()
        self.assertTrue(user.check_password("new-pass-456"))
