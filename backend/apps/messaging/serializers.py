from django.utils import timezone
from rest_framework import serializers

from .models import Interview, Message


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ("id", "task", "application", "sender", "sender_name", "recipient", "body", "created_at", "read_at")
        read_only_fields = ("id", "sender", "sender_name", "created_at", "read_at")

    def get_sender_name(self, obj):
        return " ".join(part for part in (obj.sender.first_name, obj.sender.last_name) if part).strip() or obj.sender.email

    def validate(self, attrs):
        request = self.context["request"]
        task = attrs["task"]
        recipient = attrs["recipient"]
        application = attrs.get("application")
        if request.user.role == "CLIENT" and task.owner_id != request.user.id:
            raise serializers.ValidationError("Clients may only message on their own jobs.")
        if request.user.role == "CLIENT" and application is None:
            raise serializers.ValidationError("Clients must select an application when messaging a worker.")
        if request.user.role == "WORKER":
            if not task.applications.filter(worker=request.user).exists():
                raise serializers.ValidationError("Workers may only message on jobs they applied to.")
            if application is not None and application.worker_id != request.user.id:
                raise serializers.ValidationError("Workers may only message on their own application.")
            if recipient.id != task.owner_id:
                raise serializers.ValidationError("Workers may only message the client who owns the job.")
        if request.user.role == "CLIENT" and recipient.id != application.worker_id:
            raise serializers.ValidationError("Clients may only message the worker on the selected application.")
        if recipient.id == request.user.id:
            raise serializers.ValidationError("You cannot message yourself.")
        if application and application.task_id != task.id:
            raise serializers.ValidationError("The application must belong to the selected job.")
        return attrs


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = ("id", "application", "organizer", "starts_at", "ends_at", "location", "notes", "status", "created_at")
        read_only_fields = ("id", "organizer", "status", "created_at")

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", self.instance.starts_at if self.instance else None)
        ends_at = attrs.get("ends_at", self.instance.ends_at if self.instance else None)
        if ends_at <= starts_at:
            raise serializers.ValidationError("Interview end time must be after the start time.")
        if starts_at <= timezone.now():
            raise serializers.ValidationError("Interview start time must be in the future.")
        application = attrs.get("application", self.instance.application if self.instance else None)
        request = self.context["request"]
        if request.user.role == "WORKER":
            raise serializers.ValidationError("Only the client who owns the job may schedule an interview.")
        if request.user.role == "CLIENT" and application.task.owner_id != request.user.id:
            raise serializers.ValidationError("You may only schedule interviews for your own jobs.")
        if request.user.role == "WORKER" and application.worker_id != request.user.id:
            raise serializers.ValidationError("You may only view your own interviews.")
        return attrs
