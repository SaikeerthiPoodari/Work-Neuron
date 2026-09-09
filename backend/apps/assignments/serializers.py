from rest_framework import serializers

from .models import Assignment


class AssignmentSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only=True)
    worker_email = serializers.EmailField(source="worker.email", read_only=True)
    task_status = serializers.CharField(source="task.status", read_only=True)

    class Meta:
        model = Assignment
        fields = (
            "id", "task", "task_title", "task_status", "worker_email", "application", "progress", "submission",
            "client_feedback", "started_at", "submitted_at", "completed_at", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "task", "task_title", "task_status", "worker_email", "application", "progress", "submission",
            "started_at", "submitted_at", "completed_at", "created_at", "updated_at",
        )


class ProgressSerializer(serializers.Serializer):
    progress = serializers.IntegerField(min_value=0, max_value=100)


class SubmissionSerializer(serializers.Serializer):
    submission = serializers.CharField(allow_blank=False, trim_whitespace=True)


class CompletionSerializer(serializers.Serializer):
    client_feedback = serializers.CharField(required=False, allow_blank=True)

