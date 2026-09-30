from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class AdminAnalyticsApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user("analytics-admin@example.com", password="test-pass-123", role=User.Role.ADMIN)
        self.client_user = User.objects.create_user("analytics-client@example.com", password="test-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user("analytics-worker@example.com", password="test-pass-123", role=User.Role.WORKER)

    def test_admin_can_request_each_supported_range(self):
        self.client.force_authenticate(self.admin)
        for period in ("7d", "30d", "3m", "6m", "1y"):
            with self.subTest(period=period):
                response = self.client.get(f"/api/analytics/summary/?range={period}")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["range"], period)
                self.assertIn("trend", response.data["tasks"])
                self.assertIn("growth", response.data["users"])

    def test_worker_and_client_cannot_access_analytics(self):
        for user in (self.worker, self.client_user):
            with self.subTest(role=user.role):
                self.client.force_authenticate(user)
                response = self.client.get("/api/analytics/summary/?range=7d")
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_range_is_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/analytics/summary/?range=all")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
