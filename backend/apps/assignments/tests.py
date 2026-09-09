from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application
from apps.tasks.models import Task

from .models import Assignment


class AssignmentApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.other_worker = User.objects.create_user(email="other@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(
            owner=self.client_user,
            title="Implement service",
            description="Implement the service.",
            budget="1000.00",
            deadline=timezone.now() + timedelta(days=5),
            status=Task.Status.ASSIGNED,
        )
        application = Application.objects.create(task=self.task, worker=self.worker, cover_letter="I can help.", status=Application.Status.ACCEPTED)
        self.assignment = Assignment.objects.create(task=self.task, worker=self.worker, application=application)

    def test_worker_can_start_update_progress_and_submit(self):
        self.client.force_authenticate(user=self.worker)
        start = self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        self.assertEqual(start.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.IN_PROGRESS)

        progress = self.client.patch(
            reverse("assignment-progress", kwargs={"pk": self.assignment.id}), {"progress": 60}, format="json"
        )
        self.assertEqual(progress.status_code, status.HTTP_200_OK)
        self.assertEqual(progress.data["progress"], 60)

        submitted = self.client.post(
            reverse("assignment-submit", kwargs={"pk": self.assignment.id}), {"submission": "Completed implementation."}, format="json"
        )
        self.assertEqual(submitted.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.SUBMITTED)
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.progress, 100)

    def test_only_assigned_worker_can_update_progress(self):
        self.client.force_authenticate(user=self.other_worker)
        response = self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_can_complete_submitted_assignment(self):
        self.task.status = Task.Status.SUBMITTED
        self.task.save(update_fields=["status"])
        self.assignment.submission = "Ready for review."
        self.assignment.save(update_fields=["submission"])
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(
            reverse("assignment-complete", kwargs={"pk": self.assignment.id}), {"client_feedback": "Accepted."}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.COMPLETED)
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.client_feedback, "Accepted.")
        self.assertIsNotNone(self.assignment.completed_at)

