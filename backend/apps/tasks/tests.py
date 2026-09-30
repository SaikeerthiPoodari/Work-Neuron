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
            category=overrides.get("category", ""),
            job_type=overrides.get("job_type", Task.JobType.FREELANCE),
            deadline=overrides.get("deadline", timezone.now() + timedelta(days=5)),
            location=overrides.get("location", "Hyderabad"),
            latitude=overrides.get("latitude"),
            longitude=overrides.get("longitude"),
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

    def test_worker_can_filter_by_job_type_and_category(self):
        self.create_task(title="Weekend retail shift", category="Retail", job_type=Task.JobType.WEEKEND)
        self.create_task(title="Full time engineering", category="Engineering", job_type=Task.JobType.FULL_TIME)
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-list-create"), {"job_type": Task.JobType.WEEKEND, "category": "retail"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["title"] for item in response.data], ["Weekend retail shift"])

    def test_worker_can_filter_verified_employer_and_sort_by_salary(self):
        from apps.employers.models import EmployerVerification
        EmployerVerification.objects.create(employer=self.client_user, legal_name="Verified Co", employer_type="COMPANY", business_address="Hyderabad", contact_phone="9000000000", status=EmployerVerification.Status.VERIFIED)
        self.create_task(title="Lower salary", budget="100.00")
        self.create_task(title="Higher salary", budget="500.00")
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-list-create"), {"verified": "true", "education": "", "sort": "salary"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "Higher salary")

    def test_special_job_section_returns_only_its_job_type(self):
        self.create_task(title="Weekend retail shift", job_type=Task.JobType.WEEKEND)
        self.create_task(title="Daily helper", job_type=Task.JobType.DAILY_WAGE)
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("weekend-jobs"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["title"] for item in response.data], ["Weekend retail shift"])

    def test_worker_can_search_nearby_jobs_by_distance(self):
        self.create_task(title="Nearby", location="Hyderabad", latitude="17.385044", longitude="78.486671")
        self.create_task(title="Far away", location="Delhi", latitude="28.613939", longitude="77.209023")
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-list-create"), {"latitude": "17.385044", "longitude": "78.486671", "radius_km": "10"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "Nearby")
        self.assertIn("distance_km", response.data[0])

    def test_nearby_search_returns_each_valid_job_coordinate(self):
        expected = {
            "West": ("17.385044", "78.486671"),
            "North": ("17.410000", "78.490000"),
            "South": ("17.360000", "78.470000"),
        }
        for title, (latitude, longitude) in expected.items():
            self.create_task(title=title, latitude=latitude, longitude=longitude)
        # A legacy invalid location should be skipped without affecting valid rows.
        self.create_task(title="Invalid legacy coordinate", latitude="95.000000", longitude="78.000000")
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-list-create"), {"latitude": "17.385044", "longitude": "78.486671", "radius_km": "10"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({item["title"] for item in response.data}, set(expected))
        self.assertTrue(all(item["latitude"] and item["longitude"] and item["distance_km"] is not None for item in response.data))

    def test_remote_jobs_remain_eligible_in_nearby_search(self):
        self.create_task(title="Remote role", location="Remote", work_mode=Task.WorkMode.REMOTE, is_remote=True)
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-list-create"), {"latitude": "17.385044", "longitude": "78.486671", "radius_km": "5"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], "Remote role")
        self.assertIsNone(response.data[0]["distance_km"])

    def test_end_date_cannot_precede_start_date(self):
        self.client.force_authenticate(user=self.client_user)
        payload = {**self.payload, "start_date": "2026-10-20", "end_date": "2026-10-19"}
        response = self.client.post(reverse("task-list-create"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("End date cannot be before start date", str(response.data))

    def test_on_site_task_requires_city_and_location(self):
        self.client.force_authenticate(user=self.client_user)
        payload = {**self.payload, "work_mode": Task.WorkMode.ONSITE}
        response = self.client.post(reverse("task-list-create"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

    def test_task_decomposition_returns_steps_and_required_skill_matches(self):
        task = self.create_task(description="Build the Python API. Test the endpoint.")
        TaskSkill.objects.create(task=task, skill=self.python)
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse("task-decomposition", kwargs={"pk": task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["steps"]), 2)
        self.assertEqual(response.data["steps"][0]["matched_skills"][0]["name"], "Python")

    def test_worker_cannot_decompose_closed_task(self):
        task = self.create_task(status=Task.Status.CANCELLED)
        self.client.force_authenticate(user=self.worker)
        response = self.client.get(reverse("task-decomposition", kwargs={"pk": task.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
