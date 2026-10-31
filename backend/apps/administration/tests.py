from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.accounts.models import User
from .models import AuditEvent


class AdministrationApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="admin@example.com", password="secure-pass-123")
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)

    def test_admin_can_list_and_deactivate_user(self):
        self.client.force_authenticate(user=self.admin)
        listed = self.client.get(reverse("admin-user-list"))
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(listed.data), 2)

        updated = self.client.patch(reverse("admin-user-detail", kwargs={"pk": self.worker.id}), {"is_active": False}, format="json")
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.worker.refresh_from_db()
        self.assertFalse(self.worker.is_active)

    def test_non_admin_cannot_access_admin_or_analytics_endpoints(self):
        self.client.force_authenticate(user=self.worker)
        admin_response = self.client.get(reverse("admin-task-list"))
        analytics_response = self.client.get(reverse("analytics-summary"))
        self.assertEqual(admin_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(analytics_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_read_analytics_summary(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("analytics-summary"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["users"]["admins"], 1)
        self.assertIn("by_status", response.data["tasks"])
        self.assertIn("verified_amount", response.data["transactions"])

    def test_admin_user_list_supports_safe_filters(self):
        inactive = User.objects.create_user(email="inactive@example.com", password="secure-pass-123", role=User.Role.CLIENT, is_active=False)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("admin-user-list"), {"role": "CLIENT", "active": "false", "search": "inactive"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [inactive.id])

    def test_sensitive_user_changes_are_audited_and_listed(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(reverse("admin-user-detail", kwargs={"pk": self.worker.id}), {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event = AuditEvent.objects.get(action="USER_ACCOUNT_UPDATED", target_id=str(self.worker.id))
        audit = self.client.get(reverse("admin-audit-event-list"))
        self.assertEqual(audit.status_code, status.HTTP_200_OK)
        self.assertEqual(audit.data[0]["id"], event.id)

