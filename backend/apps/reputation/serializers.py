from rest_framework import serializers

from .models import ReputationScore


class ReputationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ReputationScore
        fields = (
            "user", "user_email", "average_rating", "completed_tasks", "total_tasks", "completion_rate",
            "response_rate", "complaint_health", "score", "updated_at",
        )
        read_only_fields = fields

