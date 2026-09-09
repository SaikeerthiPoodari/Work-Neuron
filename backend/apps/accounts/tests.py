from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthenticationApiTests(APITestCase):
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

