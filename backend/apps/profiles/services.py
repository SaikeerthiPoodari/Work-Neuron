from django.db.models import Avg
from django.utils import timezone

from .models import ProfessionalPortfolio


def refresh_professional_portfolio(worker):
    """Generate only from verified/completed WorkNeuron records.

    A configured AI provider can replace this function later; the fallback is
    deterministic and never invents experience or achievements.
    """
    from apps.assignments.models import Assignment
    from apps.reviews.models import Review

    completed_assignments = list(
        Assignment.objects.filter(worker=worker, task__status="COMPLETED")
        .select_related("task", "task__owner", "task__owner__client_profile")
        .prefetch_related("task__skills")
        .order_by("completed_at", "id")
    )
    completed = len(completed_assignments)
    profile = getattr(worker, "worker_profile", None)
    skills = list(worker.worker_skills.select_related("skill").values_list("skill__name", flat=True))
    reviews = Review.objects.filter(reviewed_user=worker, reviewer__role="CLIENT", assignment__task__status="COMPLETED")
    average_rating = reviews.aggregate(value=Avg("rating"))["value"]
    skill_text = ", ".join(skills[:8]) or "verified professional skills"
    headline = profile.headline if profile and profile.headline else "WorkNeuron professional"
    years = profile.experience_years if profile else 0
    summary = f"{headline} with {years} year{'s' if years != 1 else ''} of experience, focused on {skill_text}."
    if completed:
        categories = list(dict.fromkeys(item.task.category for item in completed_assignments if item.task.category))
        category_text = f" across {', '.join(categories[:3])}" if categories else ""
        summary += f" Completed {completed} verified WorkNeuron assignment{'s' if completed != 1 else ''}{category_text}."
    if average_rating is not None:
        summary += f" Client feedback averages {average_rating:.1f}/5 from {reviews.count()} verified review{'s' if reviews.count() != 1 else ''}."
    elif not completed:
        summary += " A verified WorkNeuron work history will appear here as completed assignments are recorded."
    portfolio, _ = ProfessionalPortfolio.objects.get_or_create(worker=worker)
    portfolio.summary = summary
    portfolio.generated_at = timezone.now()
    portfolio.source_assignment_count = completed
    portfolio.save(update_fields=["summary", "generated_at", "source_assignment_count", "updated_at"])
    return portfolio
