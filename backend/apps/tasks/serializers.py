from django.utils import timezone
from rest_framework import serializers

from apps.skills.models import Skill
from apps.skills.serializers import SkillSerializer
from apps.employers.models import EmployerVerification

from .models import Task, TaskSkill


class TaskSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    required_skills = SkillSerializer(source="skills", many=True, read_only=True)
    employer_verification = serializers.SerializerMethodField()
    skill_ids = serializers.PrimaryKeyRelatedField(
        source="skills", many=True, queryset=Skill.objects.filter(is_active=True), write_only=True, required=False
    )

    class Meta:
        model = Task
        fields = (
            "id", "owner_email", "employer_verification", "title", "description", "required_skills", "skill_ids", "budget", "category",
            "job_type", "salary_type", "education_requirement", "experience_requirement", "working_hours",
            "start_date", "end_date", "deadline", "location", "location_address", "location_city", "location_area", "location_state", "location_description", "latitude", "longitude", "is_remote", "work_mode", "availability_requirements", "status", "created_at", "updated_at",
        )
        read_only_fields = ("id", "owner_email", "employer_verification", "required_skills", "status", "created_at", "updated_at")

    def get_employer_verification(self, obj):
        verification = getattr(obj.owner, "employer_verification", None)
        if verification is None:
            return {"status": EmployerVerification.Status.UNVERIFIED, "badge_text": ""}
        return {"status": verification.status, "badge_text": verification.badge_text, "employer_type": verification.employer_type}

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Task title cannot be blank.")
        return value.strip()

    def validate_deadline(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Deadline must be in the future.")
        return value

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")
        work_mode = attrs.get("work_mode", getattr(self.instance, "work_mode", Task.WorkMode.REMOTE))
        location = attrs.get("location", getattr(self.instance, "location", ""))
        address = attrs.get("location_address", getattr(self.instance, "location_address", ""))
        city = attrs.get("location_city", getattr(self.instance, "location_city", ""))
        if work_mode == Task.WorkMode.ONSITE and not ((address or location) and city):
            raise serializers.ValidationError("On-site jobs require an address or location and a city.")
        return attrs

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
