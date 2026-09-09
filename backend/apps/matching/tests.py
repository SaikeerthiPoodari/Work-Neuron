from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.profiles.models import WorkerProfile
from apps.skills.models import Skill, WorkerSkill
from apps.tasks.models import Task, TaskSkill
from ai_engine.matching.scoring import score_worker_for_task


class FakeEmbedder:
    def encode(self, texts):
        return [[1.0, 0.0] for _ in texts]


class MatchingEngineTests(APITestCase):
    def test_score_contains_explainable_components_and_uses_skill_overlap(self):
        client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        WorkerProfile.objects.create(user=worker, bio="Builds Django APIs", experience_years=5, location="Remote")
        skill = Skill.objects.create(name="Django")
        WorkerSkill.objects.create(worker=worker, skill=skill, proficiency=5, years_experience=5)
        task = Task.objects.create(
            owner=client_user,
            title="Django API",
            description="Build a Django service.",
            budget="1000.00",
            deadline=timezone.now() + timedelta(days=5),
            location="Remote",
        )
        TaskSkill.objects.create(task=task, skill=skill)
        result = score_worker_for_task(task, worker, embedder=FakeEmbedder())
        self.assertEqual(result["skill_score"], 100.0)
        self.assertEqual(result["semantic_score"], 100.0)
        self.assertGreater(result["overall_score"], 50)
        self.assertIn("Django", result["explanation"])
        self.assertIn("weights", result)


class MatchingApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(
            owner=self.client_user,
            title="Recommended task",
            description="Task for recommendation.",
            budget="1000.00",
            deadline=timezone.now() + timedelta(days=5),
        )
        self.score = {
            "overall_score": 87.0,
            "skill_score": 100.0,
            "semantic_score": 90.0,
            "experience_score": 70.0,
            "rating_score": 50.0,
            "availability_score": 100.0,
            "location_score": 100.0,
            "reputation_score": 50.0,
            "weights": {"semantic": 0.45},
            "explanation": "Strong match.",
        }

    @patch("apps.matching.views.score_worker_for_task")
    def test_task_owner_can_view_ranked_worker_matches(self, score_mock):
        score_mock.return_value = self.score
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse("task-worker-matches", kwargs={"pk": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["worker"]["email"], self.worker.email)
        self.assertEqual(response.data[0]["match"]["overall_score"], 87.0)

    def test_worker_cannot_view_client_worker_matches(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-worker-matches", kwargs={"pk": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

