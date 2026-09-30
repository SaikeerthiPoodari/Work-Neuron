from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["is_active", "name"])]

    def __str__(self):
        return self.name


class WorkerSkill(models.Model):
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="worker_skills")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="worker_skills")
    proficiency = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    years_experience = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(80)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["skill__name"]
        constraints = [models.UniqueConstraint(fields=["worker", "skill"], name="unique_worker_skill")]

    def __str__(self):
        return f"{self.worker.email} - {self.skill.name}"


class WorkerSkillHistory(models.Model):
    """Actual profile snapshots; history begins when a worker changes a skill."""
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skill_history")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="worker_history")
    proficiency = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    years_experience = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(80)])
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["recorded_at"]
        indexes = [models.Index(fields=["worker", "recorded_at"])]

    def __str__(self):
        return f"{self.worker.email} · {self.skill.name} ({self.proficiency}/5)"
