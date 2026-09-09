from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ClientProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_profile")
    organization_name = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=160, blank=True)
    website = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Client profile: {self.user.email}"


class WorkerProfile(models.Model):
    class Availability(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full time"
        PART_TIME = "PART_TIME", "Part time"
        WEEKENDS = "WEEKENDS", "Weekends"
        FLEXIBLE = "FLEXIBLE", "Flexible"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="worker_profile")
    headline = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(80)])
    location = models.CharField(max_length=160, blank=True)
    availability = models.CharField(max_length=20, choices=Availability.choices, default=Availability.FLEXIBLE)
    portfolio_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Worker profile: {self.user.email}"

