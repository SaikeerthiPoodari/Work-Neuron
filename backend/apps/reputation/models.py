from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ReputationScore(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reputation_score")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    completed_tasks = models.PositiveIntegerField(default=0)
    total_tasks = models.PositiveIntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    response_rate = models.DecimalField(max_digits=5, decimal_places=2, default=100, validators=[MinValueValidator(0), MaxValueValidator(100)])
    complaint_health = models.DecimalField(max_digits=5, decimal_places=2, default=100, validators=[MinValueValidator(0), MaxValueValidator(100)])
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Reputation: {self.user.email} ({self.score})"

