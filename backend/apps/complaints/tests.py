from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.tasks.models import Task
from apps.notifications.models import Notification

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

    def test_worker_can_report_a_suspicious_job(self):
        task = Task.objects.create(owner=self.subject, title="Suspicious job", description="Details", budget="100.00", deadline=timezone.now() + timedelta(days=2))
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("complaint-list-create"), {"category": "JOB_REPORT", "report_reason": Complaint.ReportReason.SCAM, "task": task.id, "description": "This listing asks for an upfront fee."}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Notification.objects.filter(recipient=self.admin, kind=Notification.Kind.REPORT_RECEIVED).exists())

    def test_duplicate_job_reports_are_rejected_until_dismissed(self):
        task = Task.objects.create(owner=self.subject, title="Repeated listing", description="Details", budget="100.00", deadline=timezone.now() + timedelta(days=2))
        self.client.force_authenticate(user=self.user)
        payload = {"category": "JOB_REPORT", "report_reason": Complaint.ReportReason.FAKE, "task": task.id, "description": "Suspicious."}
        self.assertEqual(self.client.post(reverse("complaint-list-create"), payload, format="json").status_code, status.HTTP_201_CREATED)
        duplicate = self.client.post(reverse("complaint-list-create"), payload, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_dismissal_records_resolver(self):
        task = Task.objects.create(owner=self.subject, title="Reportable", description="Details", budget="100.00", deadline=timezone.now() + timedelta(days=2))
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("complaint-list-create"), {"category": "JOB_REPORT", "report_reason": Complaint.ReportReason.OTHER, "task": task.id, "description": "Needs review."}, format="json")
        self.client.force_authenticate(user=self.admin)
        update = self.client.patch(reverse("complaint-detail", kwargs={"pk": response.data["id"]}), {"status": Complaint.Status.DISMISSED, "resolution_notes": "Insufficient evidence."}, format="json")
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(Complaint.objects.get(pk=response.data["id"]).resolved_by, self.admin)
