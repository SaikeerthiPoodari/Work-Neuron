from rest_framework import serializers

from apps.accounts.models import User
from .models import AuditEvent


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role", "is_active", "is_staff", "date_joined")
        read_only_fields = ("id", "email", "date_joined")


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditEvent
        fields = ("id", "actor_email", "action", "target_type", "target_id", "metadata", "ip_address", "created_at")
        read_only_fields = fields

