from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        APPLICATION_RECEIVED = "APPLICATION_RECEIVED", "Application received"
        APPLICATION_ACCEPTED = "APPLICATION_ACCEPTED", "Application accepted"
        APPLICATION_REJECTED = "APPLICATION_REJECTED", "Application rejected"
        APPLICATION_WITHDRAWN = "APPLICATION_WITHDRAWN", "Application withdrawn"
        TASK_ASSIGNED = "TASK_ASSIGNED", "Task assigned"
        TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED", "Task status changed"
        TASK_SUBMITTED = "TASK_SUBMITTED", "Task submitted"
        TASK_COMPLETED = "TASK_COMPLETED", "Task completed"
        REVIEW_RECEIVED = "REVIEW_RECEIVED", "Review received"
        PAYMENT_UPDATE = "PAYMENT_UPDATE", "Payment update"
        REPORT_RECEIVED = "REPORT_RECEIVED", "Report received"
        VERIFICATION_UPDATE = "VERIFICATION_UPDATE", "Verification update"

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=160)
    message = models.TextField()
    related_url = models.CharField(max_length=255, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "read_at", "created_at"])]

    def __str__(self):
        return f"{self.recipient.email}: {self.title}"
