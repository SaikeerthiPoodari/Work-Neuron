from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application
from apps.tasks.models import Task

from .models import Assignment, AssignmentLevel


class AssignmentApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.other_client = User.objects.create_user(email="other-client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.other_worker = User.objects.create_user(email="other@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(owner=self.client_user, title="Implement service", description="Implement the service.", budget="1000.00", deadline=timezone.now() + timedelta(days=5), status=Task.Status.ASSIGNED)
        application = Application.objects.create(task=self.task, worker=self.worker, cover_letter="I can help.", status=Application.Status.ACCEPTED)
        self.assignment = Assignment.objects.create(task=self.task, worker=self.worker, application=application)

    def configure(self):
        self.client.force_authenticate(user=self.client_user)
        return self.client.put(reverse("assignment-levels-config", kwargs={"pk": self.assignment.id}), {"levels": [
            {"title": "Planning", "description": "Clarify the scope", "requirements": "Provide an approved plan"},
            {"title": "Delivery", "description": "Build the solution", "requirements": "Provide working code"},
        ]}, format="json")

    def test_worker_cannot_skip_locked_levels_and_client_review_unlocks_next(self):
        self.assertEqual(self.configure().status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.worker)
        started = self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        self.assertEqual(started.status_code, status.HTTP_200_OK)
        levels = started.data["levels"]
        self.assertEqual([level["status"] for level in levels], ["CURRENT", "LOCKED"])

        submit = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"submission": "Plan attached"}, format="json")
        self.assertEqual(submit.status_code, status.HTTP_200_OK)
        self.assertEqual([level["status"] for level in submit.data["levels"]], ["SUBMITTED", "LOCKED"])
        self.assertEqual(submit.data["progress"], 0)

        self.client.force_authenticate(user=self.other_worker)
        forbidden = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"submission": "wrong user"}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.other_client)
        forbidden = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"action": "approve"}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.client_user)
        review = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"action": "approve", "feedback": "Good plan"}, format="json")
        self.assertEqual(review.status_code, status.HTTP_200_OK)
        self.assertEqual([level["status"] for level in review.data["levels"]], ["COMPLETED", "CURRENT"])
        self.assertEqual(review.data["progress"], 50)

    def test_final_stage_review_completes_task_and_assignment(self):
        self.assertEqual(self.configure().status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.worker)
        self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        first = self.assignment.levels.get(order=1)
        self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": first.id}), {"submission": "Plan ready"}, format="json")
        self.client.force_authenticate(user=self.client_user)
        self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": first.id}), {"action": "approve"}, format="json")
        last = self.assignment.levels.get(order=2)
        self.client.force_authenticate(user=self.worker)
        submitted = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": last.id}), {"submission": "Delivery ready"}, format="json")
        self.assertEqual(submitted.status_code, status.HTTP_200_OK)
        self.assertEqual(submitted.data["task_status"], Task.Status.SUBMITTED)
        self.client.force_authenticate(user=self.client_user)
        completed = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": last.id}), {"action": "approve", "feedback": "Accepted"}, format="json")
        self.assertEqual(completed.status_code, status.HTTP_200_OK)
        self.assertEqual(completed.data["progress"], 100)
        self.task.refresh_from_db()
        self.assignment.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(self.assignment.completed_at)

    def test_levels_can_only_be_configured_by_owner_before_start(self):
        self.client.force_authenticate(user=self.other_client)
        forbidden = self.client.put(reverse("assignment-levels-config", kwargs={"pk": self.assignment.id}), {"levels": [{"title": "Stage"}]}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.configure().status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.worker)
        self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        self.client.force_authenticate(user=self.client_user)
        locked = self.client.put(reverse("assignment-levels-config", kwargs={"pk": self.assignment.id}), {"levels": [{"title": "Changed"}]}, format="json")
        self.assertEqual(locked.status_code, status.HTTP_400_BAD_REQUEST)
