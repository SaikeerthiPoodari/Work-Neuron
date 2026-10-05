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
        if request.user.role == "CLIENT" and task.owner_id != request.user.id:
            raise serializers.ValidationError("Clients may only message on their own jobs.")
        if request.user.role == "WORKER" and not task.applications.filter(worker=request.user).exists():
            raise serializers.ValidationError("Workers may only message on jobs they applied to.")
        if recipient.id == request.user.id:
            raise serializers.ValidationError("You cannot message yourself.")
        if attrs.get("application") and attrs["application"].task_id != task.id:
            raise serializers.ValidationError("The application must belong to the selected job.")
        return attrs


class InterviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interview
        fields = ("id", "application", "organizer", "starts_at", "ends_at", "location", "notes", "status", "created_at")
        read_only_fields = ("id", "organizer", "status", "created_at")

    def validate(self, attrs):
        if attrs["ends_at"] <= attrs["starts_at"]:
            raise serializers.ValidationError("Interview end time must be after the start time.")
        if attrs["starts_at"] <= timezone.now():
            raise serializers.ValidationError("Interview start time must be in the future.")
        application = attrs["application"]
        request = self.context["request"]
        if request.user.role == "CLIENT" and application.task.owner_id != request.user.id:
            raise serializers.ValidationError("You may only schedule interviews for your own jobs.")
        if request.user.role == "WORKER" and application.worker_id != request.user.id:
            raise serializers.ValidationError("You may only view your own interviews.")
        return attrs
