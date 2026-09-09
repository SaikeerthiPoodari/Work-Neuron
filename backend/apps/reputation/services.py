from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Avg, Count, Q

from apps.assignments.models import Assignment
from apps.reviews.models import Review

from .models import ReputationScore


def update_reputation(user):
    received = Review.objects.filter(reviewed_user=user)
    average = received.aggregate(value=Avg("rating"))["value"] or Decimal("0")
    if user.role == user.Role.WORKER:
        total_tasks = Assignment.objects.filter(worker=user).count()
    elif user.role == user.Role.CLIENT:
        total_tasks = Assignment.objects.filter(task__owner=user).count()
    else:
        total_tasks = 0
    completed_tasks = Assignment.objects.filter(
        Q(worker=user) | Q(task__owner=user), task__status="COMPLETED"
    ).distinct().count()
    completion_rate = (Decimal(completed_tasks) / Decimal(total_tasks) * 100) if total_tasks else Decimal("0")
    # Response and complaint event data are introduced in later phases. Until then, response is neutral/available
    # and complaint health is perfect by absence of complaint records, both explicitly visible in the API.
    response_rate = Decimal("100")
    complaint_health = Decimal("100")
    score = (
        (Decimal(average) / Decimal("5") * Decimal("50"))
        + (completion_rate * Decimal("0.30"))
        + (response_rate * Decimal("0.10"))
        + (complaint_health * Decimal("0.10"))
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    reputation, _ = ReputationScore.objects.get_or_create(user=user)
    reputation.average_rating = Decimal(average).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    reputation.completed_tasks = completed_tasks
    reputation.total_tasks = total_tasks
    reputation.completion_rate = completion_rate.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    reputation.response_rate = response_rate
    reputation.complaint_health = complaint_health
    reputation.score = max(Decimal("0"), min(Decimal("100"), score))
    reputation.save()
    return reputation

