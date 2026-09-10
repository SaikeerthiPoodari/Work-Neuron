from rest_framework import serializers

from .models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    complainant_email = serializers.EmailField(source="complainant.email", read_only=True)

    class Meta:
        model = Complaint
        fields = (
            "id", "complainant_email", "category", "subject_user", "task", "application", "assignment", "transaction",
            "description", "status", "resolution_notes", "created_at", "updated_at",
        )
        read_only_fields = ("id", "complainant_email", "status", "resolution_notes", "created_at", "updated_at")

    def validate(self, attrs):
        if not any(attrs.get(field) for field in ("subject_user", "task", "application", "assignment", "transaction")):
            raise serializers.ValidationError("A complaint must reference a user, task, application, assignment, or payment.")
        return attrs


class ComplaintAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ("id", "status", "resolution_notes")
        read_only_fields = ("id",)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.status == Complaint.Status.RESOLVED:
            instance.resolved_by = self.context["request"].user
            instance.save(update_fields=["resolved_by", "updated_at"])
        return instance

