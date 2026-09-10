from django.conf import settings
from django.db import models


class FraudAlert(models.Model):
    class AlertType(models.TextChoices):
        HIGH_APPLICATION_ACTIVITY = "HIGH_APPLICATION_ACTIVITY", "High application activity"
        REPEATED_COMPLAINTS = "REPEATED_COMPLAINTS", "Repeated complaints"
        UNUSUAL_TRANSACTION_ACTIVITY = "UNUSUAL_TRANSACTION_ACTIVITY", "Unusual transaction activity"
        SUSPICIOUS_RATING_PATTERN = "SUSPICIOUS_RATING_PATTERN", "Suspicious rating pattern"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        REVIEWED = "REVIEWED", "Reviewed"
        DISMISSED = "DISMISSED", "Dismissed"

    alert_type = models.CharField(max_length=40, choices=AlertType.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="fraud_alerts")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    evidence = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["alert_type", "user", "status"], name="unique_open_fraud_alert_type_user_status")]
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["alert_type", "score"])]

