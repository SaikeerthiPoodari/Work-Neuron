from rest_framework import serializers

from .models import ClientProfile, WorkerProfile
from .languages import LANGUAGES


class ClientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ClientProfile
        fields = ("id", "email", "organization_name", "bio", "phone", "location", "website", "employer_type", "updated_at")
        read_only_fields = ("id", "email", "updated_at")


class WorkerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    languages = serializers.ListField(child=serializers.ChoiceField(choices=LANGUAGES), required=False)

    class Meta:
        model = WorkerProfile
        fields = (
            "id", "email", "headline", "bio", "experience_years", "location",
            "availability", "portfolio_url", "profile_photo_url", "education", "interests", "languages", "preferred_job_type", "preferred_salary",
            "preferred_working_hours", "updated_at",
            "current_city", "current_area", "current_state", "latitude", "longitude", "preferred_radius_km",
            "preferred_job_location", "remote_preference",
        )
        read_only_fields = ("id", "email", "updated_at")

    def validate(self, attrs):
        latitude = attrs.get("latitude", getattr(self.instance, "latitude", None))
        longitude = attrs.get("longitude", getattr(self.instance, "longitude", None))
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError("Latitude and longitude must be provided together, or both cleared.")
        return attrs

    def validate_languages(self, value):
        return list(dict.fromkeys(value))
