import asyncio

from channels.testing import WebsocketCommunicator
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TransactionTestCase

from apps.accounts.models import User
from config.asgi import application
from rest_framework_simplejwt.tokens import AccessToken

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

    def test_communication_notification_kinds_are_supported(self):
        message = create_notification(
            self.user,
            Notification.Kind.MESSAGE_RECEIVED,
            "New message",
            "A client sent you a message.",
        )
        interview = create_notification(
            self.user,
            Notification.Kind.INTERVIEW_SCHEDULED,
            "Interview scheduled",
            "Your interview is scheduled.",
        )
        self.assertEqual(message.kind, "MESSAGE_RECEIVED")
        self.assertEqual(interview.kind, "INTERVIEW_SCHEDULED")



class NotificationWebsocketTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(email="socket@example.com", password="secure-pass-123", role=User.Role.WORKER)

    def test_authenticated_websocket_accepts_ping(self):
        token = str(AccessToken.for_user(self.user))

        async def exercise():
            communicator = WebsocketCommunicator(application, f"/ws/notifications/?token={token}")
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            self.assertEqual(await communicator.receive_json_from(), {"type": "connected"})
            await communicator.send_json_to({"action": "ping"})
            self.assertEqual(await communicator.receive_json_from(), {"type": "pong"})
            await communicator.disconnect()

        asyncio.run(exercise())

