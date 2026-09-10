from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.assignments.models import Assignment


class Transaction(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        VERIFIED = "VERIFIED", "Verified"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, related_name="transactions")
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments_made")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="INR")
    provider = models.CharField(max_length=30, default="RAZORPAY_TEST")
    provider_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    provider_payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["assignment", "status"]), models.Index(fields=["payer", "status"])]

