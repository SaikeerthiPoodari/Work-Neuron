from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .models import EmployerVerification


class EmployerVerificationApiTests(APITestCase):
    def setUp(self):
        self.employer = User.objects.create_user(email="employer@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.admin = User.objects.create_superuser(email="admin@example.com", password="secure-pass-123")
        self.payload = {
            "legal_name": "Bright Local Foods Pvt Ltd",
            "business_name": "Bright Local Foods",
            "employer_type": "SUPERMARKET",
            "business_address": "12 Market Road, Hyderabad",
            "contact_phone": "+91 9000000000",
            "website": "https://example.com",
            "registration_number": "REG-123",
        }

    def test_employer_can_submit_and_read_pending_verification(self):
        self.client.force_authenticate(user=self.employer)
        response = self.client.post(reverse("employer-verification"), self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], EmployerVerification.Status.PENDING)
        read = self.client.get(reverse("employer-verification"))
        self.assertEqual(read.data["status"], EmployerVerification.Status.PENDING)

    def test_worker_cannot_submit_verification(self):
        self.client.force_authenticate(user=self.worker)
        response = self.client.post(reverse("employer-verification"), self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_approve_reject_and_suspend(self):
        verification = EmployerVerification.objects.create(employer=self.employer, status=EmployerVerification.Status.PENDING, **self.payload)
        self.client.force_authenticate(user=self.admin)
        listing = self.client.get(reverse("admin-verification-list"), {"status": "PENDING"})
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listing.data), 1)
        approved = self.client.post(reverse("admin-verification-action", kwargs={"pk": verification.id}), {"action": "approve", "admin_notes": "Reviewed registration."}, format="json")
        self.assertEqual(approved.data["status"], EmployerVerification.Status.VERIFIED)
        self.assertEqual(approved.data["badge_text"], "Verified Supermarket")
        suspended = self.client.post(reverse("admin-verification-action", kwargs={"pk": verification.id}), {"action": "suspend"}, format="json")
        self.assertEqual(suspended.data["status"], EmployerVerification.Status.SUSPENDED)

    def test_non_admin_cannot_review_verification(self):
        verification = EmployerVerification.objects.create(employer=self.employer, status=EmployerVerification.Status.PENDING, **self.payload)
        self.client.force_authenticate(user=self.employer)
        response = self.client.post(reverse("admin-verification-action", kwargs={"pk": verification.id}), {"action": "approve"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_document_upload_is_owner_only_and_size_limited(self):
        verification = EmployerVerification.objects.create(employer=self.employer, status=EmployerVerification.Status.PENDING, **self.payload)
        self.client.force_authenticate(user=self.employer)
        upload = SimpleUploadedFile("registration.pdf", b"pdf-content", content_type="application/pdf")
        response = self.client.post(reverse("employer-verification-document"), {"label": "Registration", "file": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(user=self.worker)
        forbidden = self.client.post(reverse("employer-verification-document"), {"label": "Other", "file": upload}, format="multipart")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
