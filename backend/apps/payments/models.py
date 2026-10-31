from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.assignments.models import Assignment


class Transaction(models.Model):
    class EscrowStatus(models.TextChoices):
        PENDING = "PENDING", "Awaiting payment"
        HELD = "HELD", "Held in escrow"
        RELEASED = "RELEASED", "Released to worker"
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
    escrow_status = models.CharField(max_length=10, choices=EscrowStatus.choices, default=EscrowStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["assignment", "status"]), models.Index(fields=["payer", "status"])]


class PaymentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_profile")
    qr_token = models.CharField(max_length=96, unique=True)
    qr_revoked = models.BooleanField(default=False)
    pin_hash = models.CharField(max_length=128, blank=True)
    pin_attempts = models.PositiveSmallIntegerField(default=0)
    pin_locked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BankAccount(models.Model):
    class VerificationStatus(models.TextChoices):
        DEMO = "DEMO", "Demo verified"
        PENDING = "PENDING", "Pending verification"
        VERIFIED = "VERIFIED", "Verified"
        FAILED = "FAILED", "Verification failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bank_accounts")
    holder_name = models.CharField(max_length=120)
    bank_name = models.CharField(max_length=120)
    account_number = models.CharField(max_length=34)
    ifsc_code = models.CharField(max_length=20)
    account_type = models.CharField(max_length=20, default="SAVINGS")
    upi_id = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)
    verification_status = models.CharField(max_length=10, choices=VerificationStatus.choices, default=VerificationStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "-created_at"]
        indexes = [models.Index(fields=["user", "is_primary"])]


class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods")
    method_type = models.CharField(max_length=30)
    provider_reference = models.CharField(max_length=160, blank=True)
    display_label = models.CharField(max_length=120)
    verification_status = models.CharField(max_length=10, default="PENDING")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_primary", "-created_at"]


class PayoutRecord(models.Model):
    class Status(models.TextChoices):
        PROCESSING = "PROCESSING", "Processing"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"

    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name="payout_record")
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payout_records")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, related_name="payouts")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PROCESSING)
    provider_reference = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

