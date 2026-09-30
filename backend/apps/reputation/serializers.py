from rest_framework import serializers
from django.db.models import Count
from apps.reviews.models import Review

from .models import ReputationScore


class ReputationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    review_count = serializers.SerializerMethodField()
    rating_distribution = serializers.SerializerMethodField()

    class Meta:
        model = ReputationScore
        fields = (
            "user", "user_email", "average_rating", "review_count", "rating_distribution", "completed_tasks", "total_tasks", "completion_rate",
            "response_rate", "complaint_health", "score", "updated_at",
        )
        read_only_fields = fields

    def get_review_count(self, obj):
        return Review.objects.filter(reviewed_user=obj.user).count()

    def get_rating_distribution(self, obj):
        counts = {item["rating"]: item["count"] for item in Review.objects.filter(reviewed_user=obj.user).values("rating").annotate(count=Count("id"))}
        return {str(star): counts.get(star, 0) for star in range(1, 6)}
