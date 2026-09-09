from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.tasks.models import Task


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="applications")
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="applications")
    cover_letter = models.TextField()
    proposed_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["task", "worker"], name="unique_task_worker_application")]
        indexes = [models.Index(fields=["task", "status"]), models.Index(fields=["worker", "status"])]

    def __str__(self):
        return f"{self.worker.email} -> {self.task.title}"

