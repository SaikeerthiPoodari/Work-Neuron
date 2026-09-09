from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.skills.models import Skill

from .models import Task, TaskSkill


class TaskApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.other_client = User.objects.create_user(email="other@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.admin = User.objects.create_superuser(email="admin@example.com", password="secure-pass-123")
        self.python = Skill.objects.create(name="Python", category="Programming")
        self.django = Skill.objects.create(name="Django", category="Programming")
        self.payload = {
            "title": "Build an API",
            "description": "Create a maintainable REST API for a marketplace.",
            "skill_ids": [self.python.id, self.django.id],
            "budget": "15000.00",
            "deadline": (timezone.now() + timedelta(days=7)).isoformat(),
            "location": "Remote",
            "availability_requirements": "Part-time evenings",
        }

    def create_task(self, owner=None, **overrides):
        task = Task.objects.create(
            owner=owner or self.client_user,
            title=overrides.get("title", "Existing task"),
            description=overrides.get("description", "Task description"),
            budget=overrides.get("budget", "500.00"),
            deadline=overrides.get("deadline", timezone.now() + timedelta(days=5)),
            location=overrides.get("location", "Hyderabad"),
            status=overrides.get("status", Task.Status.OPEN),
        )
        return task

    def test_client_can_create_task_with_required_skills(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.post(reverse("task-list-create"), self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task = Task.objects.get(title="Build an API")
        self.assertEqual(task.owner, self.client_user)
        self.assertEqual(set(task.skills.values_list("id", flat=True)), {self.python.id, self.django.id})
        self.assertEqual(response.data["status"], Task.Status.OPEN)
        self.assertEqual(len(response.data["required_skills"]), 2)

    def test_only_clients_can_create_tasks(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("task-list-create"), self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_workers_can_search_and_filter_open_tasks(self):
        self.create_task(title="Python API", location="Remote", budget="1000.00")
        second = self.create_task(title="Design logo", location="Delhi", budget="200.00")
        TaskSkill.objects.create(task=second, skill=self.django)
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-list-create"), {"search": "Python", "min_budget": "500", "location": "remote"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Python API")

    def test_invalid_state_transition_is_rejected_and_valid_sequence_works(self):
        task = self.create_task()
        self.client.force_authenticate(user=self.client_user)
        invalid = self.client.post(reverse("task-transition", kwargs={"pk": task.id}), {"status": Task.Status.COMPLETED}, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Task.objects.get(pk=task.id).status, Task.Status.OPEN)

        for next_status in (
            Task.Status.APPLICATIONS_RECEIVED,
            Task.Status.ASSIGNED,
            Task.Status.IN_PROGRESS,
            Task.Status.SUBMITTED,
            Task.Status.COMPLETED,
        ):
            response = self.client.post(
                reverse("task-transition", kwargs={"pk": task.id}), {"status": next_status}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Task.objects.get(pk=task.id).status, Task.Status.COMPLETED)

        after_completion = self.client.post(
            reverse("task-transition", kwargs={"pk": task.id}), {"status": Task.Status.CANCELLED}, format="json"
        )
        self.assertEqual(after_completion.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_owner_cannot_modify_or_transition_task(self):
        task = self.create_task()
        self.client.force_authenticate(user=self.other_client)
        update = self.client.patch(reverse("task-detail", kwargs={"pk": task.id}), {"title": "Hijacked"}, format="json")
        self.assertEqual(update.status_code, status.HTTP_403_FORBIDDEN)
        transition = self.client.post(
            reverse("task-transition", kwargs={"pk": task.id}), {"status": Task.Status.CANCELLED}, format="json"
        )
        self.assertEqual(transition.status_code, status.HTTP_403_FORBIDDEN)

    def test_worker_cannot_view_closed_task(self):
        task = self.create_task(status=Task.Status.CANCELLED)
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-detail", kwargs={"pk": task.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

