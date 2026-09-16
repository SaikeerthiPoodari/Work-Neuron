from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import Skill, WorkerSkill


class SkillApiTests(APITestCase):
    def setUp(self):
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.admin = User.objects.create_superuser(email="admin@example.com", password="secure-pass-123")
        self.python_skill = Skill.objects.create(name="Python", category="Programming")

    def test_worker_can_add_and_remove_own_skill(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(
            reverse("my-skills"),
            {"skill": self.python_skill.id, "proficiency": 5, "years_experience": 4},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["skill_name"], "Python")
        relation_id = response.data["id"]

        duplicate = self.client.post(reverse("my-skills"), {"skill": self.python_skill.id}, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(WorkerSkill.objects.filter(worker=self.worker, skill=self.python_skill).count(), 1)

        removed = self.client.delete(reverse("my-skill-detail", kwargs={"pk": relation_id}))
        self.assertEqual(removed.status_code, status.HTTP_204_NO_CONTENT)

    def test_only_admin_can_create_catalog_skills(self):
        self.client.force_authenticate(user=self.worker)
        denied = self.client.post(reverse("skill-list-create"), {"name": "Django"}, format="json")
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        created = self.client.post(reverse("skill-list-create"), {"name": "Django", "category": "Programming"}, format="json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

    def test_client_cannot_manage_worker_skills(self):
        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse("my-skills"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_view_skill_graph(self):
        second_skill = Skill.objects.create(name="Django", category="Programming")
        WorkerSkill.objects.create(worker=self.worker, skill=self.python_skill)
        WorkerSkill.objects.create(worker=self.worker, skill=second_skill)

        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(reverse("skill-graph"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["nodes"]), 2)
        self.assertEqual(response.data["edges"], [{"source": self.python_skill.id, "target": second_skill.id, "weight": 1}])

    def test_skill_graph_requires_authentication(self):
        response = self.client.get(reverse("skill-graph"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
