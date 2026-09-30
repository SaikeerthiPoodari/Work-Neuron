from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.skills.models import Skill, WorkerSkill
from apps.tasks.models import Task


class WorkerSkillGapApiTests(APITestCase):
    def setUp(self):
        self.worker = User.objects.create_user("gap-worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.other_worker = User.objects.create_user("other-worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.client_user = User.objects.create_user("gap-client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.python = Skill.objects.create(name="Python", category="Engineering")
        self.django = Skill.objects.create(name="Django", category="Engineering")
        self.git = Skill.objects.create(name="Git", category="Engineering")
        self.task_one = self.make_task("API implementation", "Backend", [self.python, self.django])
        self.task_two = self.make_task("Data service", "Backend", [self.python, self.git])
        self.make_task("Campaign design", "Marketing", [self.git])

    def make_task(self, title, category, skills):
        task = Task.objects.create(owner=self.client_user, title=title, description="Work requiring listed skills.",
                                   budget="500.00", deadline=timezone.now() + timedelta(days=5), category=category)
        task.skills.set(skills)
        return task

    def analyze(self, **params):
        self.client.force_authenticate(self.worker)
        return self.client.get(reverse("worker-skill-gap"), params)

    def test_partial_match_uses_category_job_requirements_and_frequency(self):
        WorkerSkill.objects.create(worker=self.worker, skill=self.python)
        response = self.analyze(category="Backend")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["match_percentage"], 33)
        self.assertEqual([item["name"] for item in response.data["matched_skills"]], ["Python"])
        by_name = {item["name"]: item for item in response.data["missing_skills"]}
        self.assertEqual(by_name["Django"]["frequency_percent"], 50)
        self.assertEqual(by_name["Git"]["frequency_percent"], 50)
        self.assertIn("Python", response.data["explanation"])

    def test_complete_match_and_selected_task_scope(self):
        WorkerSkill.objects.create(worker=self.worker, skill=self.python)
        WorkerSkill.objects.create(worker=self.worker, skill=self.django)
        response = self.analyze(task=self.task_one.id)
        self.assertEqual(response.data["required_count"], 2)
        self.assertEqual(response.data["match_percentage"], 100)
        self.assertEqual(response.data["missing_skills"], [])

    def test_low_proficiency_match_is_flagged_for_improvement(self):
        WorkerSkill.objects.create(worker=self.worker, skill=self.python, proficiency=2)
        response = self.analyze(task=self.task_one.id)
        self.assertEqual([item["name"] for item in response.data["improve_skills"]], ["Python"])
        suggestion = next(item for item in response.data["recommendations"] if item["name"] == "Python")
        self.assertEqual(suggestion["action"], "improve")

    def test_worker_without_skills_gets_real_requirements_and_guidance(self):
        response = self.analyze(category="Backend")
        self.assertEqual(response.data["current_skills"], [])
        self.assertEqual(response.data["match_percentage"], 0)
        self.assertTrue(response.data["missing_skills"])
        self.assertIn("Add skills", response.data["message"])

    def test_category_filter_and_empty_target_are_handled(self):
        response = self.analyze(category="Marketing")
        self.assertEqual(response.data["matching_task_count"], 1)
        self.assertEqual([item["name"] for item in response.data["required_skills"]], ["Git"])
        empty = self.analyze(category="Unrepresented category")
        self.assertEqual(empty.data["required_skills"], [])
        self.assertFalse(empty.data["data_available"])

    def test_initial_response_lists_unique_categories_and_category_jobs(self):
        self.make_task("Backend API", " Backend ", [self.python])
        response = self.analyze()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["categories"], ["Backend", "Marketing"])
        backend = self.analyze(category="Backend")
        self.assertEqual({item["title"] for item in backend.data["target_tasks"]}, {"API implementation", "Data service", "Backend API"})
        selected = self.analyze(category="Backend", task=self.task_one.id)
        self.assertEqual(selected.data["target"]["task"]["id"], self.task_one.id)
        self.assertTrue(selected.data["data_available"])

    def test_analysis_is_private_to_authenticated_workers(self):
        WorkerSkill.objects.create(worker=self.other_worker, skill=self.django)
        response = self.analyze(category="Backend", worker=self.other_worker.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["current_skills"], [])
        self.client.force_authenticate(self.client_user)
        denied = self.client.get(reverse("worker-skill-gap"), {"category": "Backend"})
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
