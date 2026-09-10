from datetime import timedelta
from decimal import Decimal

from django.db.models import Count
from django.utils import timezone

from apps.applications.models import Application
from apps.complaints.models import Complaint
from apps.payments.models import Transaction
from apps.reviews.models import Review

from .models import FraudAlert


def _open_alert(alert_type, user, score, evidence):
    alert, created = FraudAlert.objects.get_or_create(
        alert_type=alert_type,
        user=user,
        status=FraudAlert.Status.OPEN,
        defaults={"score": Decimal(str(score)), "evidence": evidence},
    )
    if not created:
        alert.score = Decimal(str(score))
        alert.evidence = evidence
        alert.save(update_fields=["score", "evidence", "updated_at"])
    return alert


def scan_user(user):
    since = timezone.now() - timedelta(hours=24)
    alerts = []
    applications = Application.objects.filter(worker=user, created_at__gte=since).count()
    if applications > 20:
        alerts.append(_open_alert(FraudAlert.AlertType.HIGH_APPLICATION_ACTIVITY, user, min(100, applications * 3), {"applications_last_24h": applications, "threshold": 20}))
    complaints = Complaint.objects.filter(subject_user=user, status__in=[Complaint.Status.OPEN, Complaint.Status.UNDER_REVIEW]).count()
    if complaints >= 3:
        alerts.append(_open_alert(FraudAlert.AlertType.REPEATED_COMPLAINTS, user, min(100, complaints * 20), {"open_complaints": complaints, "threshold": 3}))
    transactions = Transaction.objects.filter(payer=user, created_at__gte=since).count()
    if transactions > 10:
        alerts.append(_open_alert(FraudAlert.AlertType.UNUSUAL_TRANSACTION_ACTIVITY, user, min(100, transactions * 5), {"transactions_last_24h": transactions, "threshold": 10}))
    ratings = list(Review.objects.filter(reviewed_user=user).values_list("rating", flat=True))
    if len(ratings) >= 5 and len(set(ratings)) == 1:
        alerts.append(_open_alert(FraudAlert.AlertType.SUSPICIOUS_RATING_PATTERN, user, 70, {"ratings": ratings, "sample_size": len(ratings)}))
    return alerts

