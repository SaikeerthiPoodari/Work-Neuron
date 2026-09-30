from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.profiles.models import ClientProfile


class EmployerVerification(models.Model):
    class Status(models.TextChoices):
        UNVERIFIED = "UNVERIFIED", "Unverified"
        PENDING = "PENDING", "Pending review"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    employer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employer_verification")
    legal_name = models.CharField(max_length=180)
    business_name = models.CharField(max_length=180, blank=True)
    employer_type = models.CharField(max_length=32, choices=ClientProfile.EmployerType.choices)
    business_address = models.CharField(max_length=300)
    contact_phone = models.CharField(max_length=30)
    recruiter_name = models.CharField(max_length=160, blank=True)
    website = models.URLField(blank=True)
    registration_number = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.UNVERIFIED)
    applicant_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="employer_reviews")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-updated_at"]
        indexes = [models.Index(fields=["status", "updated_at"]), models.Index(fields=["employer_type", "status"])]

    @property
    def badge_text(self):
        if self.status != self.Status.VERIFIED:
            return ""
        return f"Verified {self.get_employer_type_display()}"


class VerificationDocument(models.Model):
    verification = models.ForeignKey(EmployerVerification, on_delete=models.CASCADE, related_name="documents")
    label = models.CharField(max_length=120)
    file = models.FileField(
        upload_to="private/employer-verification/",
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "png", "jpg", "jpeg"])],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]
