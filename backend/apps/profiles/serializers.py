from rest_framework import serializers

from .models import ClientProfile, WorkerProfile


class ClientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ClientProfile
        fields = ("id", "email", "organization_name", "bio", "phone", "location", "website", "updated_at")
        read_only_fields = ("id", "email", "updated_at")


class WorkerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = WorkerProfile
        fields = (
            "id", "email", "headline", "bio", "experience_years", "location",
            "availability", "portfolio_url", "updated_at",
        )
        read_only_fields = ("id", "email", "updated_at")

