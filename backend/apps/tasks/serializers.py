from django.utils import timezone
from rest_framework import serializers

from apps.skills.models import Skill
from apps.skills.serializers import SkillSerializer

from .models import Task, TaskSkill


class TaskSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    required_skills = SkillSerializer(source="skills", many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        source="skills", many=True, queryset=Skill.objects.filter(is_active=True), write_only=True, required=False
    )

    class Meta:
        model = Task
        fields = (
            "id", "owner_email", "title", "description", "required_skills", "skill_ids", "budget", "deadline",
            "location", "availability_requirements", "status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "owner_email", "required_skills", "status", "created_at", "updated_at")

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Task title cannot be blank.")
        return value.strip()

    def validate_deadline(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Deadline must be in the future.")
        return value

    def validate_skill_ids(self, value):
        if len(value) != len(set(skill.id for skill in value)):
            raise serializers.ValidationError("A required skill cannot be repeated.")
        return value

    def create(self, validated_data):
        skills = validated_data.pop("skills", [])
        task = Task.objects.create(**validated_data)
        TaskSkill.objects.bulk_create([TaskSkill(task=task, skill=skill) for skill in skills])
        return task

    def update(self, instance, validated_data):
        skills = validated_data.pop("skills", None)
        instance = super().update(instance, validated_data)
        if skills is not None:
            TaskSkill.objects.filter(task=instance).delete()
            TaskSkill.objects.bulk_create([TaskSkill(task=instance, skill=skill) for skill in skills])
        return instance


class TaskTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Task.Status.choices)

