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

