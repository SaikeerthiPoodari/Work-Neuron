from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.tasks.models import Task


class RecommendationApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(
            owner=self.client_user,
            title="Feed task",
            description="Task in the worker feed.",
            budget="750.00",
            deadline=timezone.now() + timedelta(days=4),
        )

    @patch("apps.recommendations.views.score_task_for_worker")
    def test_worker_receives_smart_task_feed(self, score_mock):
        score_mock.return_value = {"overall_score": 80.0, "explanation": "Good match."}
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("smart-task-feed"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["task"]["title"], "Feed task")
        self.assertEqual(response.data[0]["match"]["overall_score"], 80.0)

    def test_client_cannot_use_worker_smart_feed(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse("smart-task-feed"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.recommendations.views.score_task_for_worker")
    def test_worker_job_recommendations_support_job_type_filter(self, score_mock):
        score_mock.return_value = {"overall_score": 91.0, "explanation": "Matches your preferences."}
        self.task.job_type = "PART_TIME"
        self.task.category = "Software"
        self.task.save(update_fields=["job_type", "category"])
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("job-recommendations"), {"job_type": "PART_TIME", "category": "software"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["task"]["title"], "Feed task")

    def test_client_cannot_use_job_recommendations(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse("job-recommendations"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.recommendations.views.score_task_for_worker")
    def test_client_can_request_worker_recommendations_for_own_task(self, score_mock):
        score_mock.return_value = {"overall_score": 75.0, "explanation": "Partial match."}
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse("worker-recommendations"), {"task": self.task.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["worker"]["email"], self.worker.email)
