from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.applications.models import Application
from apps.tasks.models import Task

from .services import update_reputation


class ReputationTests(APITestCase):
    def test_reputation_formula_exposes_provisional_response_and_complaint_inputs(self):
        client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        task = Task.objects.create(
            owner=client_user,
            title="Work",
            description="Work",
            budget="100.00",
            deadline=timezone.now() + timedelta(days=2),
            status=Task.Status.COMPLETED,
        )
        application = Application.objects.create(task=task, worker=worker, cover_letter="Done", status=Application.Status.ACCEPTED)
        Assignment.objects.create(task=task, worker=worker, application=application)
        reputation = update_reputation(worker)
        self.assertEqual(reputation.completed_tasks, 1)
        self.assertEqual(reputation.total_tasks, 1)
        self.assertEqual(reputation.response_rate, 100)
        self.assertEqual(reputation.complaint_health, 100)
        self.assertEqual(reputation.score, 50)

    def test_authenticated_user_can_view_another_users_reputation(self):
        user = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse("user-reputation", kwargs={"user_id": user.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user_email"], user.email)
