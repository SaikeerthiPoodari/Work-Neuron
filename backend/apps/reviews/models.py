from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.assignments.models import Assignment


class Review(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="written_reviews")
    reviewed_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="received_reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["assignment", "reviewer", "reviewed_user"], name="unique_assignment_review_direction")]
        indexes = [models.Index(fields=["reviewed_user", "created_at"])]

    def __str__(self):
        return f"{self.reviewer.email} reviewed {self.reviewed_user.email}"

