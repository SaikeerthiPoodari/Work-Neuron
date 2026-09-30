from rest_framework import serializers

from .models import Assignment, AssignmentLevel, AssignmentLevelTask


class AssignmentLevelTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentLevelTask
        fields = ("id", "title", "is_completed", "completed_at")


class AssignmentLevelSerializer(serializers.ModelSerializer):
    tasks = AssignmentLevelTaskSerializer(source="checklist_items", many=True, read_only=True)
    class Meta:
        model = AssignmentLevel
        fields = ("id", "order", "title", "description", "requirements", "status", "submission", "feedback", "submitted_at", "reviewed_at", "tasks")
        read_only_fields = ("id", "status", "submission", "feedback", "submitted_at", "reviewed_at")


class AssignmentLevelInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=180)
    description = serializers.CharField(required=False, allow_blank=True)
    requirements = serializers.CharField(required=False, allow_blank=True)
    tasks = serializers.ListField(child=serializers.CharField(max_length=240, trim_whitespace=True), required=False, allow_empty=True, max_length=30)


class AssignmentLevelsConfigSerializer(serializers.Serializer):
    levels = AssignmentLevelInputSerializer(many=True, min_length=1, max_length=30)


class LevelSubmissionSerializer(serializers.Serializer):
    submission = serializers.CharField(allow_blank=False, trim_whitespace=True)


class LevelReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("approve", "changes"))
    feedback = serializers.CharField(required=False, allow_blank=True)


class AssignmentSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only=True)
    worker_email = serializers.EmailField(source="worker.email", read_only=True)
    task_status = serializers.CharField(source="task.status", read_only=True)
    levels = AssignmentLevelSerializer(many=True, read_only=True)
    current_level = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = (
            "id", "task", "task_title", "task_status", "worker_email", "application", "progress", "submission",
            "client_feedback", "started_at", "submitted_at", "completed_at", "created_at", "updated_at", "levels", "current_level",
        )
        read_only_fields = (
            "id", "task", "task_title", "task_status", "worker_email", "application", "progress", "submission",
            "client_feedback", "started_at", "submitted_at", "completed_at", "created_at", "updated_at", "levels", "current_level",
        )

    def get_current_level(self, obj):
        level = next((item for item in obj.levels.all() if item.status in (AssignmentLevel.Status.CURRENT, AssignmentLevel.Status.SUBMITTED)), None)
        return AssignmentLevelSerializer(level).data if level else None


class ProgressSerializer(serializers.Serializer):
    progress = serializers.IntegerField(min_value=0, max_value=100)


class SubmissionSerializer(serializers.Serializer):
    submission = serializers.CharField(allow_blank=False, trim_whitespace=True)


class CompletionSerializer(serializers.Serializer):
    client_feedback = serializers.CharField(required=False, allow_blank=True)
