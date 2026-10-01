from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.skills.models import Skill


class Task(models.Model):
    class SkillLevel(models.TextChoices):
        LEVEL_1 = "LEVEL_1", "Level 1"
        LEVEL_2 = "LEVEL_2", "Level 2"
        LEVEL_3 = "LEVEL_3", "Level 3"
    class WorkMode(models.TextChoices):
        REMOTE = "REMOTE", "Remote"
        ONSITE = "ONSITE", "On-site"
        HYBRID = "HYBRID", "Hybrid"

    class JobType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full time"
        PART_TIME = "PART_TIME", "Part time"
        DAILY_WAGE = "DAILY_WAGE", "Daily wage"
        WEEKEND = "WEEKEND", "Weekend"
        EVENT = "EVENT", "Event"
        FESTIVAL = "FESTIVAL", "Festival"
        CONTRACT = "CONTRACT", "Contract"
        FREELANCE = "FREELANCE", "Freelance"
        TEMPORARY = "TEMPORARY", "Temporary"
        INTERNSHIP = "INTERNSHIP", "Internship"

    class SalaryType(models.TextChoices):
        MONTHLY = "MONTHLY", "Monthly"
        DAILY = "DAILY", "Daily"
        HOURLY = "HOURLY", "Hourly"
        FIXED = "FIXED", "Fixed"
        NEGOTIABLE = "NEGOTIABLE", "Negotiable"

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
    category = models.CharField(max_length=80, blank=True)
    skill_level = models.CharField(max_length=10, choices=SkillLevel.choices, default=SkillLevel.LEVEL_1)
    required_languages = models.JSONField(default=list, blank=True)
    job_type = models.CharField(max_length=20, choices=JobType.choices, default=JobType.FREELANCE)
    salary_type = models.CharField(max_length=20, choices=SalaryType.choices, default=SalaryType.FIXED)
    education_requirement = models.CharField(max_length=160, blank=True)
    experience_requirement = models.CharField(max_length=160, blank=True)
    working_hours = models.CharField(max_length=160, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    deadline = models.DateTimeField()
    location = models.CharField(max_length=160, blank=True)
    location_address = models.CharField(max_length=240, blank=True)
    location_city = models.CharField(max_length=100, blank=True)
    location_area = models.CharField(max_length=100, blank=True)
    location_state = models.CharField(max_length=100, blank=True)
    location_description = models.CharField(max_length=240, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    is_remote = models.BooleanField(default=False)
    work_mode = models.CharField(max_length=10, choices=WorkMode.choices, default=WorkMode.REMOTE)
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
            models.Index(fields=["job_type", "status"]),
            models.Index(fields=["category", "status"]),
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
