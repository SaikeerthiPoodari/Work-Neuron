from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ClientProfile(models.Model):
    class EmployerType(models.TextChoices):
        COMPANY = "COMPANY", "Company"
        STORE = "STORE", "Store"
        RESTAURANT = "RESTAURANT", "Restaurant"
        MALL = "MALL", "Mall"
        SUPERMARKET = "SUPERMARKET", "Supermarket"
        EVENT_ORGANIZER = "EVENT_ORGANIZER", "Event organizer"
        CALL_CENTER = "CALL_CENTER", "Call center"
        DELIVERY_BUSINESS = "DELIVERY_BUSINESS", "Delivery business"
        RECRUITER = "RECRUITER", "Recruiter"
        LOCAL_BUSINESS = "LOCAL_BUSINESS", "Local business"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_profile")
    organization_name = models.CharField(max_length=160, blank=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=160, blank=True)
    website = models.URLField(blank=True)
    employer_type = models.CharField(max_length=24, choices=EmployerType.choices, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Client profile: {self.user.email}"


class WorkerProfile(models.Model):
    class RemotePreference(models.TextChoices):
        REMOTE = "REMOTE", "Remote"
        ONSITE = "ONSITE", "On-site"
        HYBRID = "HYBRID", "Hybrid"
        ANY = "ANY", "Any"

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
    profile_photo_url = models.URLField(blank=True)
    education = models.CharField(max_length=160, blank=True)
    interests = models.TextField(blank=True)
    languages = models.JSONField(default=list, blank=True)
    preferred_job_type = models.CharField(max_length=20, blank=True)
    preferred_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    preferred_working_hours = models.CharField(max_length=160, blank=True)
    current_city = models.CharField(max_length=100, blank=True)
    current_area = models.CharField(max_length=100, blank=True)
    current_state = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    preferred_radius_km = models.PositiveIntegerField(default=25, validators=[MinValueValidator(1), MaxValueValidator(500)])
    preferred_job_location = models.CharField(max_length=160, blank=True)
    remote_preference = models.CharField(max_length=10, choices=RemotePreference.choices, default=RemotePreference.ANY)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Worker profile: {self.user.email}"
