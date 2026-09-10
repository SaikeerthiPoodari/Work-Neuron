from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.accounts.models import User

from .models import Complaint


class ComplaintApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.subject = User.objects.create_user(email="subject@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.admin = User.objects.create_superuser(email="admin@example.com", password="secure-pass-123")

    def test_user_can_raise_complaint_and_admin_can_resolve(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("complaint-list-create"),
            {"category": "USER", "subject_user": self.subject.id, "description": "Suspicious communication."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        complaint_id = response.data["id"]

        self.client.force_authenticate(user=self.admin)
        update = self.client.patch(
            reverse("complaint-detail", kwargs={"pk": complaint_id}),
            {"status": Complaint.Status.RESOLVED, "resolution_notes": "Reviewed and resolved."},
            format="json",
        )
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        complaint = Complaint.objects.get(pk=complaint_id)
        self.assertEqual(complaint.status, Complaint.Status.RESOLVED)
        self.assertEqual(complaint.resolved_by, self.admin)

    def test_complaint_requires_subject_reference(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("complaint-list-create"), {"category": "USER", "description": "Missing subject."}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

