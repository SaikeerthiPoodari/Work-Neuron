from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Notification
from .services import create_notification


class NotificationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.other = User.objects.create_user(email="other@example.com", password="secure-pass-123", role=User.Role.CLIENT)

    def test_notification_is_persisted_and_can_be_marked_read(self):
        notification = create_notification(
            self.user,
            Notification.Kind.TASK_ASSIGNED,
            "Task assigned",
            "You have a new assignment.",
            "/assignments/1",
        )
        self.client.force_authenticate(user=self.user)
        listed = self.client.get(reverse("notification-list"), {"unread": "true"})
        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data[0]["id"], notification.id)

        read = self.client.post(reverse("notification-read", kwargs={"pk": notification.id}))
        self.assertEqual(read.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

        unread = self.client.get(reverse("notification-list"), {"unread": "true"})
        self.assertEqual(unread.data, [])

    def test_users_cannot_read_each_others_notifications(self):
        notification = Notification.objects.create(
            recipient=self.user,
            kind=Notification.Kind.PAYMENT_UPDATE,
            title="Payment",
            message="Payment updated.",
        )
        self.client.force_authenticate(user=self.other)
        response = self.client.post(reverse("notification-read", kwargs={"pk": notification.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

