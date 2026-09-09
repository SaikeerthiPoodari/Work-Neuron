from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.tasks.models import Task

from .models import Application


class ApplicationApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.other_worker = User.objects.create_user(email="other@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(
            owner=self.client_user,
            title="Build dashboard",
            description="Create a dashboard.",
            budget="1000.00",
            deadline=timezone.now() + timedelta(days=5),
        )

    def test_worker_can_apply_once_and_task_receives_applications_status(self):
        self.client.force_authenticate(user=self.worker)
        payload = {"task": self.task.id, "cover_letter": "I can deliver this dashboard.", "proposed_budget": "900.00"}
        response = self.client.post(reverse("application-list-create"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.get(pk=self.task.id).status, Task.Status.APPLICATIONS_RECEIVED)

        duplicate = self.client.post(reverse("application-list-create"), payload, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Application.objects.filter(task=self.task, worker=self.worker).count(), 1)

    def test_client_can_accept_application_and_assignment_is_created(self):
        application = Application.objects.create(task=self.task, worker=self.worker, cover_letter="Ready to help.")
        self.task.status = Task.Status.APPLICATIONS_RECEIVED
        self.task.save(update_fields=["status"])
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(
            reverse("application-decide", kwargs={"pk": application.id}), {"action": "accept"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.task.refresh_from_db()
        self.assertEqual(application.status, Application.Status.ACCEPTED)
        self.assertEqual(self.task.status, Task.Status.ASSIGNED)
        self.assertTrue(Assignment.objects.filter(task=self.task, worker=self.worker, application=application).exists())
        self.assertEqual(response.data["assignment_id"], Assignment.objects.get(task=self.task).id)

    def test_only_task_owner_can_decide_and_worker_can_withdraw(self):
        application = Application.objects.create(task=self.task, worker=self.worker, cover_letter="Ready to help.")
        self.client.force_authenticate(user=self.other_worker)
        denied = self.client.post(reverse("application-decide", kwargs={"pk": application.id}), {"action": "reject"}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.worker)
        withdrawn = self.client.post(reverse("application-withdraw", kwargs={"pk": application.id}))
        self.assertEqual(withdrawn.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.status, Application.Status.WITHDRAWN)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.OPEN)

