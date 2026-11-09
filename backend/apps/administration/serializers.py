from rest_framework import serializers

from apps.accounts.models import User
from .models import AuditEvent
from apps.profiles.photo import profile_photo_url


class AdminUserSerializer(serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role", "profile_photo", "is_active", "is_staff", "date_joined")
        read_only_fields = ("id", "email", "date_joined")

    def get_profile_photo(self, obj):
        return profile_photo_url(obj, self.context.get("request"))


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditEvent
        fields = ("id", "actor_email", "action", "target_type", "target_id", "metadata", "ip_address", "created_at")
        read_only_fields = fields

