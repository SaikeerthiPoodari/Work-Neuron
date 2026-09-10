from django.conf import settings
from django.db import models


class Complaint(models.Model):
    class Category(models.TextChoices):
        USER = "USER", "User"
        TASK = "TASK", "Task"
        APPLICATION = "APPLICATION", "Application"
        ASSIGNMENT = "ASSIGNMENT", "Assignment"
        PAYMENT = "PAYMENT", "Payment"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        UNDER_REVIEW = "UNDER_REVIEW", "Under review"
        RESOLVED = "RESOLVED", "Resolved"

    complainant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="complaints_made")
    category = models.CharField(max_length=20, choices=Category.choices)
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

