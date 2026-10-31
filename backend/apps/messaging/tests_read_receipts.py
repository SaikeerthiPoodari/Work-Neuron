from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application
from apps.tasks.models import Task

from .models import Message


class MessageReadReceiptTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="read-client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="read-worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(owner=self.client_user, title="Read receipt task", description="Task", budget="100", deadline=timezone.now() + timedelta(days=2))
        self.application = Application.objects.create(task=self.task, worker=self.worker, cover_letter="Ready")
        self.message = Message.objects.create(task=self.task, application=self.application, sender=self.client_user, recipient=self.worker, body="Hello")

    def test_recipient_can_mark_message_read(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("message-read", kwargs={"pk": self.message.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.message.refresh_from_db()
        self.assertIsNotNone(self.message.read_at)

    def test_sender_cannot_mark_message_read(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse("message-read", kwargs={"pk": self.message.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
