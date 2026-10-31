from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.profiles.models import WorkerProfile

from .models import Connection, DirectMessage, Follow, Post


class NetworkApiTests(APITestCase):
    def setUp(self):
        self.worker = User.objects.create_user("worker@example.com", password="secure-pass-123", role=User.Role.WORKER, first_name="Asha")
        self.client_user = User.objects.create_user("client@example.com", password="secure-pass-123", role=User.Role.CLIENT, first_name="Ravi")
        self.other = User.objects.create_user("other@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.client.force_authenticate(self.worker)

    def test_feed_post_like_save_comment_and_share(self):
        created = self.client.post(reverse("network-feed"), {"kind": "PROJECT", "title": "Portfolio project", "body": "Built a scheduling workflow.", "portfolio_url": "https://example.com/project"}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        post_id = created.data["id"]
        self.assertEqual(self.client.post(reverse("network-post-action", args=[post_id, "like"])).data["liked"], True)
        self.assertEqual(self.client.post(reverse("network-post-action", args=[post_id, "save"])).data["saved"], True)
        comment = self.client.post(reverse("network-post-comments", args=[post_id]), {"body": "Excellent work."}, format="json")
        self.assertEqual(comment.status_code, status.HTTP_201_CREATED, comment.data)
        self.assertEqual(self.client.post(reverse("network-post-action", args=[post_id, "share"])).status_code, status.HTTP_200_OK)

    def test_follow_and_connection_permissions(self):
        follow = self.client.post(reverse("network-follow", args=[self.other.id]))
        self.assertEqual(follow.status_code, status.HTTP_200_OK)
        self.assertTrue(Follow.objects.filter(follower=self.worker, following=self.other).exists())
        request = self.client.post(reverse("network-connections"), {"user_id": self.client_user.id}, format="json")
        self.assertEqual(request.status_code, status.HTTP_201_CREATED)
        connection = Connection.objects.get(requester=self.worker, recipient=self.client_user)
        self.client.force_authenticate(self.other)
        denied = self.client.post(reverse("network-connection-action", args=[connection.id, "accept"]))
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.client_user)
        accepted = self.client.post(reverse("network-connection-action", args=[connection.id, "accept"]))
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.data["status"], Connection.Status.ACCEPTED)

    def test_discover_excludes_current_user_and_supports_search(self):
        response = self.client.get(reverse("network-discover"), {"q": "Ravi"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [self.client_user.id])

    def test_connected_users_can_exchange_direct_messages(self):
        connection = Connection.objects.create(requester=self.worker, recipient=self.client_user, status=Connection.Status.ACCEPTED)
        response = self.client.post(reverse("network-direct-messages"), {"recipient": self.client_user.id, "body": "Let us collaborate."}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DirectMessage.objects.filter(sender=self.worker, recipient=self.client_user).exists())
        self.assertEqual(self.client.post(reverse("network-direct-message-read", args=[response.data["id"]])).status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(self.client_user)
        self.assertEqual(self.client.post(reverse("network-direct-message-read", args=[response.data["id"]])).status_code, status.HTTP_200_OK)

    def test_unconnected_users_cannot_direct_message(self):
        response = self.client.post(reverse("network-direct-messages"), {"recipient": self.client_user.id, "body": "Not allowed yet."}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_overview_returns_bio_posts_and_relationships(self):
        profile = WorkerProfile.objects.create(user=self.worker, bio="I build useful tools for local businesses.")
        Post.objects.create(author=self.worker, kind=Post.Kind.CERTIFICATION, title="Django certificate", body="Completed backend certification.")
        Follow.objects.create(follower=self.client_user, following=self.worker)
        response = self.client.get(reverse("network-profile-overview", args=[self.worker.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["profile"]["bio"], "I build useful tools for local businesses.")
        self.assertEqual(len(response.data["posts"]), 1)
        self.assertEqual(len(response.data["followers"]), 1)
