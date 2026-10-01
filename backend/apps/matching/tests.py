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
from ai_engine.embeddings.service import EmbeddingUnavailableError
from ai_engine.matching.scoring import score_worker_for_task, _worker_text


class FakeEmbedder:
    def encode(self, texts):
        return [[1.0, 0.0] for _ in texts]


class MatchingEngineTests(APITestCase):
    def test_selected_worker_languages_are_included_in_matching_profile_text(self):
        worker = User.objects.create_user(email="language-worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        WorkerProfile.objects.create(user=worker, languages=["en", "ta", "fr"])
        self.assertIn("English, Tamil, French", _worker_text(worker))

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

    def test_score_includes_job_preference_components(self):
        client_user = User.objects.create_user(email="client2@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        worker = User.objects.create_user(email="worker2@example.com", password="secure-pass-123", role=User.Role.WORKER)
        WorkerProfile.objects.create(user=worker, education="B.Tech CSE", interests="Software development", preferred_job_type="PART_TIME", preferred_salary="500.00")
        task = Task.objects.create(owner=client_user, title="Python intern", description="Software development", budget="1000.00", category="Software", job_type=Task.JobType.PART_TIME, education_requirement="B.Tech", deadline=timezone.now() + timedelta(days=5))
        result = score_worker_for_task(task, worker, embedder=FakeEmbedder())
        self.assertEqual(result["education_score"], 100.0)
        self.assertEqual(result["job_type_score"], 100.0)
        self.assertEqual(result["salary_score"], 100.0)
        self.assertIn("education", result["weights"])

    @patch("ai_engine.matching.scoring._semantic_score", side_effect=EmbeddingUnavailableError("model is not cached"))
    def test_score_falls_back_to_structured_signals_when_semantic_model_is_unavailable(self, _semantic_mock):
        client_user = User.objects.create_user(email="fallback-client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        worker = User.objects.create_user(email="fallback-worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        task = Task.objects.create(
            owner=client_user,
            title="Structured match",
            description="This is enough data for structured scoring.",
            budget="1000.00",
            deadline=timezone.now() + timedelta(days=5),
        )

        result = score_worker_for_task(task, worker)

        self.assertEqual(result["semantic_score"], 50.0)
        self.assertGreater(result["overall_score"], 0)
        self.assertIn("Semantic model unavailable", result["explanation"])


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
