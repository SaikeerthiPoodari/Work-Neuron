from rest_framework import serializers

from .models import Skill, WorkerSkill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ("id", "name", "category", "is_active", "created_at")
        read_only_fields = ("id", "created_at")


class WorkerSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = WorkerSkill
        fields = ("id", "skill", "skill_name", "proficiency", "years_experience", "created_at", "updated_at")
        read_only_fields = ("id", "skill_name", "created_at", "updated_at")

    def validate_skill(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This skill is not available for selection.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        worker = getattr(request, "user", None)
        skill = attrs.get("skill")
        if worker and worker.is_authenticated and skill:
            existing = WorkerSkill.objects.filter(worker=worker, skill=skill)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError({"skill": "You have already added this skill."})
        return attrs
