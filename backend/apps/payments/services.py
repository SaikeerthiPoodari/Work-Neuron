import os
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from .models import Transaction


class PaymentConfigurationError(RuntimeError):
    pass


def razorpay_client():
    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise PaymentConfigurationError("Razorpay TEST MODE credentials are not configured.")
    import razorpay
    return razorpay.Client(auth=(key_id, key_secret))


def amount_in_paise(amount):
    return int((Decimal(amount) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def create_test_order(assignment, payer):
    if assignment.task.status not in ("ASSIGNED", "IN_PROGRESS", "SUBMITTED", "COMPLETED"):
        raise ValidationError("Payment can only be created for an assigned task.")
    existing = assignment.transactions.filter(status__in=[Transaction.Status.CREATED, Transaction.Status.VERIFIED]).first()
    if existing:
        return existing, None
    client = razorpay_client()
    currency = os.getenv("RAZORPAY_CURRENCY", "INR")
    order = client.order.create({
        "amount": amount_in_paise(assignment.task.budget),
        "currency": currency,
        "receipt": f"workneuron-assignment-{assignment.id}",
        "notes": {"assignment_id": str(assignment.id)},
    })
    transaction = Transaction.objects.create(
        assignment=assignment,
        payer=payer,
        amount=assignment.task.budget,
        currency=currency,
        provider_order_id=order["id"],
    )
    return transaction, order


def verify_test_payment(transaction, order_id, payment_id, signature):
    if transaction.status == Transaction.Status.REFUNDED:
        raise ValidationError("A refunded transaction cannot be verified again.")
    if transaction.provider_order_id != order_id:
        raise ValidationError("Payment order does not match the transaction.")
    client = razorpay_client()
    client.utility.verify_payment_signature({
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": signature,
    })
    transaction.provider_payment_id = payment_id
    transaction.status = Transaction.Status.VERIFIED
    transaction.escrow_status = Transaction.EscrowStatus.HELD
    transaction.save(update_fields=["provider_payment_id", "status", "escrow_status", "updated_at"])
    return transaction


def release_escrow_for_assignment(assignment):
    """Release verified funds only after the assignment reaches both-party completion."""
    transactions = assignment.transactions.filter(status=Transaction.Status.VERIFIED, escrow_status=Transaction.EscrowStatus.HELD)
    updated = transactions.update(escrow_status=Transaction.EscrowStatus.RELEASED)
    return updated


def refund_test_payment(transaction):
    if transaction.status == Transaction.Status.REFUNDED:
        return transaction
    if transaction.status != Transaction.Status.VERIFIED:
        raise ValidationError("Only a verified payment can be refunded.")
    if not transaction.provider_payment_id:
        raise ValidationError("The payment provider has not supplied a payment ID for this transaction.")
    client = razorpay_client()
    client.payment.refund(transaction.provider_payment_id, {"amount": amount_in_paise(transaction.amount)})
    transaction.status = Transaction.Status.REFUNDED
    transaction.save(update_fields=["status", "updated_at"])
    return transaction

