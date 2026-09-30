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
