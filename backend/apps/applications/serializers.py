from django.utils import timezone
from rest_framework import serializers

from apps.tasks.models import Task

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only=True)
    worker_email = serializers.EmailField(source="worker.email", read_only=True)

    class Meta:
        model = Application
        fields = (
            "id", "task", "task_title", "worker_email", "cover_letter", "proposed_budget", "status",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "task_title", "worker_email", "status", "created_at", "updated_at")

    def validate_task(self, task):
        if task.status not in (Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED):
            raise serializers.ValidationError("Applications are closed for this task.")
        request = self.context.get("request")
        if request and task.owner_id == request.user.id:
            raise serializers.ValidationError("You cannot apply to your own task.")
        return task

    def validate_cover_letter(self, value):
        if not value.strip():
            raise serializers.ValidationError("Cover letter cannot be blank.")
        return value.strip()

    def validate(self, attrs):
        request = self.context.get("request")
        task = attrs.get("task")
        if request and task and Application.objects.filter(task=task, worker=request.user).exists():
            raise serializers.ValidationError({"task": "You have already applied to this task."})
        return attrs


class ApplicationActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("accept", "reject"))

