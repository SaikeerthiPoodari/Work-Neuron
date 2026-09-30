from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.tasks.models import Task


class Assignment(models.Model):
    task = models.OneToOneField(Task, on_delete=models.PROTECT, related_name="assignment")
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assignments")
    application = models.OneToOneField("applications.Application", on_delete=models.PROTECT, related_name="assignment")
    progress = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    submission = models.TextField(blank=True)
    client_feedback = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["worker", "updated_at"])]

    def __str__(self):
        return f"Assignment: {self.task.title}"


class AssignmentLevel(models.Model):
    class Status(models.TextChoices):
        LOCKED = "LOCKED", "Locked"
        CURRENT = "CURRENT", "Current"
        SUBMITTED = "SUBMITTED", "Submitted"
        COMPLETED = "COMPLETED", "Completed"

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="levels")
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.LOCKED)
    submission = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["assignment", "order"], name="unique_assignment_level_order")]

    def __str__(self):
        return f"{self.assignment} · Level {self.order}: {self.title}"


class AssignmentLevelTask(models.Model):
    level = models.ForeignKey(AssignmentLevel, on_delete=models.CASCADE, related_name="checklist_items")
    title = models.CharField(max_length=240)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="completed_assignment_tasks")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.title
