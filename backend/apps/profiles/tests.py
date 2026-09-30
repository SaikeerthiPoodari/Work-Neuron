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

    def test_worker_location_requires_coordinate_pair_and_can_be_cleared(self):
        self.authenticate(self.worker)
        invalid = self.client.patch(reverse("my-profile"), {"latitude": "17.3"}, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        valid = self.client.patch(reverse("my-profile"), {"current_city": "Hyderabad", "latitude": "17.3", "longitude": "78.5"}, format="json")
        self.assertEqual(valid.status_code, status.HTTP_200_OK)
        cleared = self.client.delete(reverse("my-profile"))
        self.assertEqual(cleared.status_code, status.HTTP_204_NO_CONTENT)
        profile = self.client.get(reverse("my-profile"))
        self.assertIsNone(profile.data["latitude"])
        self.assertEqual(profile.data["current_city"], "")

    def test_worker_can_save_multiple_supported_languages_and_reload_them(self):
        self.authenticate(self.worker)
        selected = ["en", "te", "hi", "fr", "ja"]
        saved = self.client.patch(reverse("my-profile"), {"languages": selected}, format="json")
        self.assertEqual(saved.status_code, status.HTTP_200_OK)
        self.assertEqual(saved.data["languages"], selected)
        reloaded = self.client.get(reverse("my-profile"))
        self.assertEqual(reloaded.data["languages"], selected)

    def test_worker_language_validation_rejects_unknown_codes(self):
        self.authenticate(self.worker)
        response = self.client.patch(reverse("my-profile"), {"languages": ["en", "xx"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
