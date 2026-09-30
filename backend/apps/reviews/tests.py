from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.applications.models import Application
from apps.tasks.models import Task

from .models import Review


class ReviewApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.outsider = User.objects.create_user(email="outsider@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(
            owner=self.client_user,
            title="Completed work",
            description="Completed task.",
            budget="1000.00",
            deadline=timezone.now() + timedelta(days=2),
            status=Task.Status.COMPLETED,
        )
        application = Application.objects.create(task=self.task, worker=self.worker, cover_letter="Done", status=Application.Status.ACCEPTED)
        self.assignment = Assignment.objects.create(task=self.task, worker=self.worker, application=application, progress=100)

    def test_client_review_updates_worker_reputation_and_worker_can_only_view(self):
        self.client.force_authenticate(user=self.client_user)
        client_review = self.client.post(
            reverse("review-list-create"),
            {"assignment": self.assignment.id, "rating": 5, "review": "Excellent work."},
            format="json",
        )
        self.assertEqual(client_review.status_code, status.HTTP_201_CREATED)
        self.assertEqual(client_review.data["reviewed_user_email"], self.worker.email)

        duplicate = self.client.post(
            reverse("review-list-create"), {"assignment": self.assignment.id, "rating": 4}, format="json"
        )
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)

        self.client.force_authenticate(user=self.worker)
        worker_review = self.client.post(
            reverse("review-list-create"), {"assignment": self.assignment.id, "rating": 4, "review": "Clear requirements."}, format="json"
        )
        self.assertEqual(worker_review.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Review.objects.filter(assignment=self.assignment).count(), 1)
        received_reviews = self.client.get(reverse("review-list-create"))
        self.assertEqual(received_reviews.status_code, status.HTTP_200_OK)
        self.assertEqual(len(received_reviews.data), 1)
        self.assertEqual(received_reviews.data[0]["client_name"], self.client_user.email)

        reputation = self.client.get(reverse("my-reputation"))
        self.assertEqual(reputation.status_code, status.HTTP_200_OK)
        self.assertEqual(reputation.data["average_rating"], "5.00")
        self.assertEqual(reputation.data["completed_tasks"], 1)
        self.assertEqual(reputation.data["score"], "100.00")

    def test_reviews_require_completed_assignment_and_participant(self):
        self.task.status = Task.Status.IN_PROGRESS
        self.task.save(update_fields=["status"])
        self.client.force_authenticate(user=self.client_user)
        incomplete = self.client.post(reverse("review-list-create"), {"assignment": self.assignment.id, "rating": 5}, format="json")
        self.assertEqual(incomplete.status_code, status.HTTP_400_BAD_REQUEST)

        self.task.status = Task.Status.COMPLETED
        self.task.save(update_fields=["status"])
        self.client.force_authenticate(user=self.outsider)
        unauthorized = self.client.post(reverse("review-list-create"), {"assignment": self.assignment.id, "rating": 5}, format="json")
        self.assertEqual(unauthorized.status_code, status.HTTP_403_FORBIDDEN)
