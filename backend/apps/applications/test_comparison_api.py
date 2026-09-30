from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.applications.models import Application
from apps.reputation.models import ReputationScore
from apps.reviews.models import Review
from apps.skills.models import Skill, WorkerSkill
from apps.tasks.models import Task


class ApplicationComparisonApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="compare-client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.other_client = User.objects.create_user(email="other-client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.workers = [User.objects.create_user(email=f"candidate-{number}@example.com", password="secure-pass-123", role=User.Role.WORKER, first_name=f"Candidate {number}") for number in range(1, 5)]
        self.task = Task.objects.create(owner=self.client_user, title="Backend API", description="Build a backend API.",
                                        budget="2500.00", deadline=timezone.now() + timedelta(days=5), category="Backend")
        self.skill = Skill.objects.create(name="Django", category="Development")
        self.task.skills.add(self.skill)
        self.client.force_authenticate(self.client_user)

    @staticmethod
    def match_result(score=80):
        return {"overall_score": score, "skill_score": 100, "semantic_score": 75, "experience_score": 60,
                "rating_score": 50, "availability_score": 100, "location_score": 80, "reputation_score": 50,
                "education_score": 100, "interest_score": 50, "job_type_score": 100, "salary_score": 90,
                "weights": {"semantic": .4, "skill": .3, "experience": .1, "rating": .05, "availability": .05,
                            "location": .025, "reputation": .025, "education": .02, "interest": .01, "job_type": .01, "salary": .01},
                "explanation": "Existing matching explanation."}

    def add_application(self, worker, budget=None):
        return Application.objects.create(task=self.task, worker=worker, cover_letter="I have relevant experience.", proposed_budget=budget)

    def test_task_with_no_applications_returns_empty_result(self):
        response = self.client.get(reverse("application-comparison", kwargs={"task_id": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["applicants"], [])

    @patch("apps.applications.views.score_worker_for_task")
    def test_one_applicant_contains_bid_skills_and_existing_match_score(self, scorer):
        scorer.return_value = self.match_result()
        application = self.add_application(self.workers[0], "1900.00")
        WorkerSkill.objects.create(worker=self.workers[0], skill=self.skill, proficiency=4, years_experience=3)
        response = self.client.get(reverse("application-comparison", kwargs={"task_id": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["eligible_applicant_count"], 1)
        candidate = response.data["applicants"][0]
        self.assertEqual(candidate["application"]["id"], application.id)
        self.assertEqual(candidate["application"]["proposed_budget"], "1900.00")
        self.assertEqual(candidate["match"]["skill_match"], 100)
        self.assertEqual(candidate["worker"]["skills"][0]["name"], "Django")
        self.assertIsNone(candidate["worker"]["rating_average"])

    @patch("apps.applications.views.score_worker_for_task")
    def test_two_applicants_are_returned_for_client_selection(self, scorer):
        scorer.side_effect = [self.match_result(score) for score in (85, 74)]
        for worker in self.workers[:2]:
            self.add_application(worker)
        response = self.client.get(reverse("application-comparison", kwargs={"task_id": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["applicants"]), 2)

    @patch("apps.applications.views.score_worker_for_task")
    def test_three_applicants_are_returned_for_client_selection(self, scorer):
        scorer.side_effect = [self.match_result(score) for score in (85, 74, 91)]
        for worker in self.workers[:3]:
            self.add_application(worker)
        response = self.client.get(reverse("application-comparison", kwargs={"task_id": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["applicants"]), 3)

    @patch("apps.applications.views.score_worker_for_task")
    def test_four_applicants_are_returned_for_client_selection(self, scorer):
        scorer.side_effect = [self.match_result(score) for score in (85, 74, 91, 65)]
        for worker in self.workers:
            self.add_application(worker)
        response = self.client.get(reverse("application-comparison", kwargs={"task_id": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["applicants"]), 4)
        self.assertIn("weights", response.data["applicants"][0]["match"])
        self.assertEqual(scorer.call_count, 4)

    def test_client_cannot_compare_another_clients_task(self):
        other_task = Task.objects.create(owner=self.other_client, title="Private task", description="Private.",
                                         budget="1000.00", deadline=timezone.now() + timedelta(days=5))
        response = self.client.get(reverse("application-comparison", kwargs={"task_id": other_task.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("apps.applications.views.score_worker_for_task")
    def test_real_rating_and_reputation_are_passed_into_existing_matcher(self, scorer):
        worker = self.workers[0]
        application = self.add_application(worker)
        previous_task = Task.objects.create(owner=self.client_user, title="Completed Backend work", description="Done.",
                                            budget="900.00", deadline=timezone.now() + timedelta(days=2),
                                            category="Backend", status=Task.Status.COMPLETED)
        previous_application = Application.objects.create(task=previous_task, worker=worker, cover_letter="Previous work")
        assignment = Assignment.objects.create(task=previous_task, worker=worker, application=previous_application)
        Review.objects.create(assignment=assignment, reviewer=self.client_user, reviewed_user=worker, rating=5)
        ReputationScore.objects.create(user=worker, average_rating="5.00", completed_tasks=1, total_tasks=1,
                                       completion_rate="100.00", score="97.00")

        def score_with_attached_data(task, candidate):
            result = self.match_result()
            result["rating_score"] = candidate._matching_rating_score
            result["reputation_score"] = candidate._matching_reputation_score
            return result

        scorer.side_effect = score_with_attached_data
        response = self.client.get(reverse("application-comparison", kwargs={"task_id": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        candidate = response.data["applicants"][0]
        self.assertEqual(candidate["worker"]["rating_average"], 5.0)
        self.assertEqual(candidate["worker"]["completed_tasks"], 1)
        self.assertEqual(candidate["worker"]["relevant_completed_tasks"], 1)
        self.assertEqual(candidate["match"]["components"]["rating_score"], 100)
        self.assertEqual(candidate["match"]["components"]["reputation_score"], 97)
        self.assertEqual(candidate["application"]["id"], application.id)

    def test_worker_cannot_use_client_comparison_endpoint(self):
        self.client.force_authenticate(self.workers[0])
        response = self.client.get(reverse("application-comparison", kwargs={"task_id": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
