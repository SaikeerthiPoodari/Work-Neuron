from rest_framework import serializers

from .models import FraudAlert


class FraudAlertSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = FraudAlert
        fields = ("id", "alert_type", "user", "user_email", "score", "evidence", "status", "resolution_notes", "created_at", "updated_at")
        read_only_fields = ("id", "alert_type", "user", "user_email", "score", "evidence", "created_at", "updated_at")

