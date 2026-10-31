from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application
from apps.notifications.models import Notification
from apps.tasks.models import Task


class MessagingApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.other_worker = User.objects.create_user(email="other@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(
            owner=self.client_user,
            title="Build a dashboard",
            description="Create a dashboard.",
            budget="1000.00",
            deadline=timezone.now() + timedelta(days=5),
        )
        self.application = Application.objects.create(task=self.task, worker=self.worker, cover_letter="Ready to help.")

    def test_client_message_notifies_selected_worker(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse("message-list-create"), {"task": self.task.id, "application": self.application.id, "recipient": self.worker.id, "body": "Are you available?"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Notification.objects.filter(recipient=self.worker, kind=Notification.Kind.MESSAGE_RECEIVED).exists())

    def test_client_cannot_message_unrelated_worker_on_application(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse("message-list-create"), {"task": self.task.id, "application": self.application.id, "recipient": self.other_worker.id, "body": "Unexpected contact"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_worker_cannot_schedule_interview(self):
        self.client.force_authenticate(user=self.worker)
        starts = (timezone.now() + timedelta(days=1)).isoformat()
        ends = (timezone.now() + timedelta(days=1, minutes=30)).isoformat()
        response = self.client.post(reverse("interview-list-create"), {"application": self.application.id, "starts_at": starts, "ends_at": ends, "location": "Online"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_scheduling_interview_notifies_worker(self):
        self.client.force_authenticate(user=self.client_user)
        starts = (timezone.now() + timedelta(days=1)).isoformat()
        ends = (timezone.now() + timedelta(days=1, minutes=30)).isoformat()
        response = self.client.post(reverse("interview-list-create"), {"application": self.application.id, "starts_at": starts, "ends_at": ends, "location": "Online"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Notification.objects.filter(recipient=self.worker, kind=Notification.Kind.INTERVIEW_SCHEDULED).exists())

    def test_client_message_requires_selected_application_and_matching_worker(self):
        self.client.force_authenticate(user=self.client_user)
        missing_application = self.client.post(reverse("message-list-create"), {
            "task": self.task.id,
            "recipient": self.worker.id,
            "body": "Please review the schedule.",
        }, format="json")
        self.assertEqual(missing_application.status_code, status.HTTP_400_BAD_REQUEST)

        mismatched_recipient = self.client.post(reverse("message-list-create"), {
            "task": self.task.id,
            "application": self.application.id,
            "recipient": self.other_worker.id,
            "body": "Please review the schedule.",
        }, format="json")
        self.assertEqual(mismatched_recipient.status_code, status.HTTP_400_BAD_REQUEST)

    def test_worker_cannot_attach_another_workers_application(self):
        other_application = Application.objects.create(task=self.task, worker=self.other_worker, cover_letter="Other application")
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("message-list-create"), {
            "task": self.task.id,
            "application": other_application.id,
            "recipient": self.client_user.id,
            "body": "This application should not be usable.",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
