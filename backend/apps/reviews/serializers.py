from rest_framework import serializers

from apps.assignments.models import Assignment

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    reviewed_user_email = serializers.EmailField(source="reviewed_user.email", read_only=True)
    assignment_title = serializers.CharField(source="assignment.task.title", read_only=True)
    task_id = serializers.IntegerField(source="assignment.task_id", read_only=True)
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "id", "assignment", "assignment_title", "task_id", "reviewer_email", "reviewer_name", "client_name", "reviewed_user_email", "rating", "review", "created_at",
        )
        read_only_fields = ("id", "reviewer_email", "reviewed_user_email", "created_at")

    def get_reviewer_name(self, obj):
        return " ".join(filter(None, [obj.reviewer.first_name, obj.reviewer.last_name])) or obj.reviewer.email

    def get_client_name(self, obj):
        user = obj.assignment.task.owner
        return " ".join(filter(None, [user.first_name, user.last_name])) or user.email

    def validate_assignment(self, assignment):
        request = self.context["request"]
        if request.user.role == "WORKER":
            raise serializers.ValidationError("Workers can view client reviews but cannot submit reviews here.")
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
