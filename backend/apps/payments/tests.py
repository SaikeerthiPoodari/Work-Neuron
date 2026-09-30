import os
import hashlib
import hmac
import json
from datetime import timedelta
from unittest.mock import Mock, patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment
from apps.notifications.models import Notification
from apps.tasks.models import Task

from .models import Transaction


class PaymentApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        task = Task.objects.create(
            owner=self.client_user,
            title="Completed deliverable",
            description="Completed work",
            budget="1234.56",
            deadline=timezone.now() + timedelta(days=2),
            status=Task.Status.COMPLETED,
        )
        application = Application.objects.create(task=task, worker=self.worker, cover_letter="Done", status=Application.Status.ACCEPTED)
        self.assignment = Assignment.objects.create(task=task, worker=self.worker, application=application, progress=100)

    def test_missing_credentials_return_configuration_error_without_fake_transaction(self):
        self.client.force_authenticate(user=self.client_user)
        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "", "RAZORPAY_KEY_SECRET": ""}, clear=False):
            response = self.client.post(reverse("payment-create-order"), {"assignment": self.assignment.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(Transaction.objects.count(), 0)

    @patch("apps.payments.services.razorpay_client")
    def test_client_can_create_test_order(self, client_factory):
        fake_client = Mock()
        fake_client.order.create.return_value = {"id": "order_test_123", "amount": 123456, "currency": "INR"}
        client_factory.return_value = fake_client
        self.client.force_authenticate(user=self.client_user)
        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "rzp_test_key", "RAZORPAY_KEY_SECRET": "secret"}, clear=False):
            response = self.client.post(reverse("payment-create-order"), {"assignment": self.assignment.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transaction = Transaction.objects.get()
        self.assertEqual(transaction.provider_order_id, "order_test_123")
        self.assertEqual(transaction.status, Transaction.Status.CREATED)
        self.assertEqual(response.data["test_mode"], True)
        self.assertEqual(response.data["key_id"], "rzp_test_key")

    @patch("apps.payments.services.razorpay_client")
    def test_payment_signature_verification_marks_transaction_verified_and_notifies_worker(self, client_factory):
        transaction = Transaction.objects.create(
            assignment=self.assignment,
            payer=self.client_user,
            amount=self.assignment.task.budget,
            provider_order_id="order_test_456",
        )
        fake_client = Mock()
        client_factory.return_value = fake_client
        self.client.force_authenticate(user=self.client_user)
        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "rzp_test_key", "RAZORPAY_KEY_SECRET": "secret"}, clear=False):
            response = self.client.post(
                reverse("payment-verify"),
                {
                    "transaction_id": transaction.id,
                    "razorpay_order_id": "order_test_456",
                    "razorpay_payment_id": "pay_test_456",
                    "razorpay_signature": "signature",
                },
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, Transaction.Status.VERIFIED)
        self.assertTrue(Notification.objects.filter(recipient=self.worker, kind=Notification.Kind.PAYMENT_UPDATE).exists())

    def test_worker_cannot_create_payment_order(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("payment-create-order"), {"assignment": self.assignment.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employer_dashboard_uses_verified_transactions_and_completed_jobs(self):
        Transaction.objects.create(
            assignment=self.assignment, payer=self.client_user, amount="1234.56",
            provider_order_id="order_dashboard", status=Transaction.Status.VERIFIED,
        )
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse("employer-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"]["total_earnings"], "1234.56")
        self.assertEqual(len(response.data["completed_jobs"]), 1)
        self.assertEqual(response.data["payment_history"][0]["status"], Transaction.Status.VERIFIED)
        self.assertIn("active_jobs", response.data)
        self.assertIn("verification", response.data)

    def test_worker_cannot_view_employer_dashboard(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("employer-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_webhook_signature_is_required_and_captured_event_is_idempotent(self):
        transaction = Transaction.objects.create(
            assignment=self.assignment, payer=self.client_user, amount="1234.56", provider_order_id="order_webhook",
        )
        payload = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {"order_id": "order_webhook", "id": "pay_webhook"}}}}).encode()
        self.client.force_authenticate(user=None)
        invalid = self.client.post(reverse("payment-webhook"), payload, content_type="application/json")
        self.assertEqual(invalid.status_code, status.HTTP_401_UNAUTHORIZED)
        signature = hmac.new(b"webhook-secret", payload, hashlib.sha256).hexdigest()
        with patch.dict(os.environ, {"RAZORPAY_WEBHOOK_SECRET": "webhook-secret"}, clear=False):
            response = self.client.post(reverse("payment-webhook"), payload, content_type="application/json", HTTP_X_RAZORPAY_SIGNATURE=signature)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, Transaction.Status.VERIFIED)
        self.assertEqual(transaction.provider_payment_id, "pay_webhook")
