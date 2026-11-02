from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("Superuser must have staff and superuser privileges.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    LANGUAGE_CHOICES = (
        ("en", "English"), ("te", "Telugu"), ("hi", "Hindi"), ("ta", "Tamil"),
        ("kn", "Kannada"), ("ml", "Malayalam"), ("bn", "Bengali"), ("mr", "Marathi"),
        ("ur", "Urdu"), ("gu", "Gujarati"), ("pa", "Punjabi"),
    )
    class Role(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        WORKER = "WORKER", "Worker"
        ADMIN = "ADMIN", "Administrator"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.WORKER)
    preferred_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default="en")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-date_joined"]
        indexes = [models.Index(fields=["role", "is_active"])]

    def __str__(self):
        return self.email

