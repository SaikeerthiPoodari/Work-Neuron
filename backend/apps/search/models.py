from django.conf import settings
from django.db import models


class SearchEvent(models.Model):
    class Kind(models.TextChoices):
        VOICE = "VOICE", "Voice search"
        RECOMMENDATION = "RECOMMENDATION", "Recommendation feed"
        VIEW = "VIEW", "Job view"
        APPLY = "APPLY", "Job application"
        COMPLETE = "COMPLETE", "Job completion"
        SAVE = "SAVE", "Saved job"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="search_events")
    task = models.ForeignKey("tasks.Task", on_delete=models.CASCADE, null=True, blank=True, related_name="interaction_events")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    language = models.CharField(max_length=20, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["kind", "created_at"])]
