from rest_framework import serializers

from apps.assignments.models import Assignment

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)
    reviewed_user_email = serializers.EmailField(source="reviewed_user.email", read_only=True)
    assignment_title = serializers.CharField(source="assignment.task.title", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id", "assignment", "assignment_title", "reviewer_email", "reviewed_user_email", "rating", "review", "created_at",
        )
        read_only_fields = ("id", "reviewer_email", "reviewed_user_email", "created_at")

    def validate_assignment(self, assignment):
        request = self.context["request"]
        if assignment.task.status != "COMPLETED":
            raise serializers.ValidationError("Reviews are available only after task completion.")
        if request.user.id not in (assignment.task.owner_id, assignment.worker_id):
            raise serializers.ValidationError("You were not part of this assignment.")
        return assignment

    def validate(self, attrs):
        request = self.context["request"]
        assignment = attrs["assignment"]
        if request.user.id == assignment.task.owner_id:
            reviewed_user_id = assignment.worker_id
        elif request.user.id == assignment.worker_id:
            reviewed_user_id = assignment.task.owner_id
        else:
            raise serializers.ValidationError("You cannot review this assignment.")
        if Review.objects.filter(assignment=assignment, reviewer=request.user, reviewed_user_id=reviewed_user_id).exists():
            raise serializers.ValidationError("You have already reviewed this assignment.")
        attrs["reviewed_user_id"] = reviewed_user_id
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        reviewed_user_id = validated_data.pop("reviewed_user_id")
        return Review.objects.create(reviewer=request.user, reviewed_user_id=reviewed_user_id, **validated_data)
