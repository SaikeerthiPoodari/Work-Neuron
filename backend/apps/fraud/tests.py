from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.complaints.models import Complaint

from .models import FraudAlert
from .services import scan_user


class FraudApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.admin = User.objects.create_superuser(email="admin@example.com", password="secure-pass-123")

    def test_repeated_complaints_create_academic_fraud_alert(self):
        for _ in range(3):
            Complaint.objects.create(
                complainant=self.admin,
                category=Complaint.Category.USER,
                subject_user=self.user,
                description="Repeated issue.",
            )
        alerts = scan_user(self.user)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, FraudAlert.AlertType.REPEATED_COMPLAINTS)
        self.assertEqual(alerts[0].status, FraudAlert.Status.OPEN)

    def test_only_admin_can_scan_and_review_alerts(self):
        self.client.force_authenticate(user=self.user)
        denied = self.client.post(reverse("fraud-scan"), {"user_id": self.user.id}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        allowed = self.client.post(reverse("fraud-scan"), {"user_id": self.user.id}, format="json")
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)

