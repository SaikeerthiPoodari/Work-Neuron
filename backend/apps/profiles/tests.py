from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class ProfileApiTests(APITestCase):
    def setUp(self):
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_worker_can_create_and_update_worker_profile(self):
        self.authenticate(self.worker)
        response = self.client.patch(
            reverse("my-profile"),
            {"headline": "Django Developer", "experience_years": 3, "availability": "PART_TIME"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["headline"], "Django Developer")
        self.assertEqual(response.data["email"], self.worker.email)

    def test_client_receives_client_profile_shape(self):
        self.authenticate(self.client_user)
        response = self.client.get(reverse("my-profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("organization_name", response.data)
        self.assertNotIn("experience_years", response.data)

    def test_admin_cannot_use_marketplace_profile_endpoint(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="secure-pass-123")
        self.authenticate(admin)
        response = self.client.get(reverse("my-profile"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

