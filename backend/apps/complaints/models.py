from django.conf import settings
from django.db import models


class Complaint(models.Model):
    class ReportReason(models.TextChoices):
        FAKE = "FAKE", "Fake or suspicious job"
        INCORRECT = "INCORRECT", "Incorrect information"
        EMPLOYER = "EMPLOYER", "Employer issue"
        INAPPROPRIATE = "INAPPROPRIATE", "Inappropriate content"
        DUPLICATE = "DUPLICATE", "Duplicate job"
        SCAM = "SCAM", "Scam or payment concern"
        OTHER = "OTHER", "Other"

    class Category(models.TextChoices):
        USER = "USER", "User"
        TASK = "TASK", "Task"
        APPLICATION = "APPLICATION", "Application"
        ASSIGNMENT = "ASSIGNMENT", "Assignment"
        PAYMENT = "PAYMENT", "Payment"
        SUPPORT = "SUPPORT", "Support request"
        JOB_REPORT = "JOB_REPORT", "Suspicious job report"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_REVIEW = "UNDER_REVIEW", "Under review"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"

    complainant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="complaints_made")
    category = models.CharField(max_length=20, choices=Category.choices)
    report_reason = models.CharField(max_length=20, choices=ReportReason.choices, blank=True)
    subject_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="complaints_received")
    task = models.ForeignKey("tasks.Task", on_delete=models.PROTECT, null=True, blank=True, related_name="complaints")
    application = models.ForeignKey("applications.Application", on_delete=models.PROTECT, null=True, blank=True, related_name="complaints")
    assignment = models.ForeignKey("assignments.Assignment", on_delete=models.PROTECT, null=True, blank=True, related_name="complaints")
    transaction = models.ForeignKey("payments.Transaction", on_delete=models.PROTECT, null=True, blank=True, related_name="complaints")
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="complaints_resolved")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["category", "status"])]
