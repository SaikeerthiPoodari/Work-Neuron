from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.skills.models import Skill


class Task(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        APPLICATIONS_RECEIVED = "APPLICATIONS_RECEIVED", "Applications received"
        ASSIGNED = "ASSIGNED", "Assigned"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        SUBMITTED = "SUBMITTED", "Submitted"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tasks")
    title = models.CharField(max_length=180)
    description = models.TextField()
    budget = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    deadline = models.DateTimeField()
    location = models.CharField(max_length=160, blank=True)
    availability_requirements = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OPEN)
    skills = models.ManyToManyField(Skill, through="TaskSkill", related_name="tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "deadline"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["location"]),
        ]
        constraints = [models.CheckConstraint(condition=models.Q(budget__gte=0), name="task_budget_non_negative")]

    def __str__(self):
        return self.title


class TaskSkill(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_skills")
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="task_skills")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["task", "skill"], name="unique_task_skill")]

    def __str__(self):
        return f"{self.task.title} - {self.skill.name}"

