from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class AssistantApiTests(APITestCase):
    def setUp(self):
        self.worker = User.objects.create_user("assistant-worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.client_user = User.objects.create_user("assistant-client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.admin = User.objects.create_user("assistant-admin@example.com", password="secure-pass-123", role=User.Role.ADMIN)

    def test_authenticated_roles_can_use_assistant(self):
        for user in (self.worker, self.client_user, self.admin):
            self.client.force_authenticate(user=user)
            response = self.client.post(reverse("assistant"), {"message": "Help me navigate WorkNeuron", "context": {"role": "ADMIN"}}, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["provider"], "fallback")

    def test_assistant_uses_authenticated_role_not_context_role(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("assistant"), {"message": "Show platform statistics", "context": {"role": "ADMIN"}}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Nora", response.data["message"])
        self.assertIn("Worker workspace", response.data["message"])
        self.assertNotIn("Admin workspace", response.data["message"])

    def test_assistant_requires_authentication(self):
        response = self.client.post(reverse("assistant"), {"message": "hello"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fallback_understands_typo_and_returns_real_worker_routes(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("assistant"), {"message": "how to aply job"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Open Find Jobs", [action["label"] for action in response.data["actions"]])
        self.assertEqual(response.data["actions"][0]["route"], "/worker/tasks")

    def test_fallback_handles_tanglish(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("assistant"), {"message": "naaku near by jobs kavali"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Mee WorkNeuron", response.data["message"])

    def test_client_does_not_receive_worker_only_job_search_action(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse("assistant"), {"message": "find jobs near me"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("/client/nearby", [action["route"] for action in response.data["actions"]])

    def test_image_attachment_is_accepted_without_being_persisted(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("assistant"), {"message": "What is this?", "media": [{"name": "sample.png", "type": "image/png", "data": "data:image/png;base64,AA=="}]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("image attachment", response.data["message"])
