from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment
from apps.reviews.models import Review
from apps.tasks.models import Task
from django.utils import timezone
from datetime import timedelta


class ProfileApiTests(APITestCase):
    def setUp(self):
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_worker_can_create_and_update_worker_profile(self):
        self.authenticate(self.worker)
        response = self.client.patch(
            reverse("my-profile"),
            {"headline": "Django Developer", "experience_years": 3, "availability": "PART_TIME"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["headline"], "Django Developer")
        self.assertEqual(response.data["email"], self.worker.email)

    def test_client_receives_client_profile_shape(self):
        self.authenticate(self.client_user)
        response = self.client.get(reverse("my-profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("organization_name", response.data)
        self.assertNotIn("experience_years", response.data)

    def test_admin_cannot_use_marketplace_profile_endpoint(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="secure-pass-123")
        self.authenticate(admin)
        response = self.client.get(reverse("my-profile"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_worker_location_requires_coordinate_pair_and_can_be_cleared(self):
        self.authenticate(self.worker)
        invalid = self.client.patch(reverse("my-profile"), {"latitude": "17.3"}, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        valid = self.client.patch(reverse("my-profile"), {"current_city": "Hyderabad", "latitude": "17.3", "longitude": "78.5"}, format="json")
        self.assertEqual(valid.status_code, status.HTTP_200_OK)
        cleared = self.client.delete(reverse("my-profile"))
        self.assertEqual(cleared.status_code, status.HTTP_204_NO_CONTENT)
        profile = self.client.get(reverse("my-profile"))
        self.assertIsNone(profile.data["latitude"])
        self.assertEqual(profile.data["current_city"], "")

    def test_worker_can_save_multiple_supported_languages_and_reload_them(self):
        self.authenticate(self.worker)
        selected = ["en", "te", "hi", "fr", "ja"]
        saved = self.client.patch(reverse("my-profile"), {"languages": selected}, format="json")
        self.assertEqual(saved.status_code, status.HTTP_200_OK)
        self.assertEqual(saved.data["languages"], selected)
        reloaded = self.client.get(reverse("my-profile"))
        self.assertEqual(reloaded.data["languages"], selected)

    def test_worker_language_validation_rejects_unknown_codes(self):
        self.authenticate(self.worker)
        response = self.client.patch(reverse("my-profile"), {"languages": ["en", "xx"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_worker_portfolio_is_readable_and_client_access_is_scoped_to_applicants(self):
        self.authenticate(self.worker)
        own = self.client.get(reverse("my-portfolio"))
        self.assertEqual(own.status_code, status.HTTP_200_OK)
        self.assertIn("summary", own.data)
        task = Task.objects.create(owner=self.client_user, title="Portfolio review", description="Review portfolio", budget="100.00", deadline=timezone.now() + timedelta(days=2))
        Application.objects.create(task=task, worker=self.worker, cover_letter="I can help.")
        self.authenticate(self.client_user)
        allowed = self.client.get(reverse("worker-portfolio", kwargs={"user_id": self.worker.id}))
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)

    def test_client_cannot_view_portfolio_for_worker_who_did_not_apply(self):
        self.authenticate(self.client_user)
        response = self.client.get(reverse("worker-portfolio", kwargs={"user_id": self.worker.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_uses_completed_assignments_and_qualifying_reviews(self):
        from apps.profiles.services import refresh_professional_portfolio

        self.worker.first_name = "Asha"
        self.worker.save(update_fields=["first_name"])
        from apps.profiles.models import WorkerProfile
        worker_profile, _ = WorkerProfile.objects.get_or_create(user=self.worker)
        worker_profile.headline = "Reliable event coordinator"
        worker_profile.experience_years = 4
        worker_profile.save(update_fields=["headline", "experience_years", "updated_at"])
        task = Task.objects.create(owner=self.client_user, title="Verified event", description="Coordinate event", category="Events", budget="100.00", deadline=timezone.now() + timedelta(days=2), status=Task.Status.COMPLETED)
        application = Application.objects.create(task=task, worker=self.worker, cover_letter="I can help.")
        assignment = Assignment.objects.create(task=task, worker=self.worker, application=application, started_at=timezone.now() - timedelta(days=3), completed_at=timezone.now())
        Review.objects.create(assignment=assignment, reviewer=self.client_user, reviewed_user=self.worker, rating=5, review="Excellent")

        portfolio = refresh_professional_portfolio(self.worker)
        self.assertIn("Completed 1 verified WorkNeuron assignment across Events.", portfolio.summary)
        self.assertIn("Client feedback averages 5.0/5 from 1 verified review.", portfolio.summary)
        self.assertEqual(portfolio.source_assignment_count, 1)
        self.authenticate(self.worker)
        response = self.client.get(reverse("my-portfolio"))
        self.assertEqual(response.data["performance"]["completed_assignments"], 1)
        self.assertEqual(response.data["reviews"][0]["rating"], 5)
        self.assertTrue(response.data["achievements"])
