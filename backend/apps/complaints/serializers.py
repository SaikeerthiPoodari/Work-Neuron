from rest_framework import serializers

from .models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    complainant_email = serializers.EmailField(source="complainant.email", read_only=True)

    class Meta:
        model = Complaint
        fields = (
            "id", "complainant_email", "category", "report_reason", "subject_user", "task", "application", "assignment", "transaction",
            "description", "status", "resolution_notes", "created_at", "updated_at",
        )
        read_only_fields = ("id", "complainant_email", "status", "resolution_notes", "created_at", "updated_at")

    def validate(self, attrs):
        category = attrs.get("category")
        task = attrs.get("task")
        if category == Complaint.Category.JOB_REPORT and not task:
            raise serializers.ValidationError({"task": "A job report must reference the job being reported."})
        if category == Complaint.Category.JOB_REPORT and not attrs.get("report_reason"):
            raise serializers.ValidationError({"report_reason": "Choose a reason for reporting this job."})
        request = self.context.get("request")
        if request and category == Complaint.Category.JOB_REPORT and task and task.owner_id == request.user.id:
            raise serializers.ValidationError({"task": "You cannot report your own job."})
        if not any(attrs.get(field) for field in ("subject_user", "task", "application", "assignment", "transaction")):
            raise serializers.ValidationError("A complaint must reference a user, task, application, assignment, or payment.")
        if request and category == Complaint.Category.JOB_REPORT and task:
            if Complaint.objects.filter(complainant=request.user, task=task, category=Complaint.Category.JOB_REPORT).exclude(status=Complaint.Status.DISMISSED).exists():
                raise serializers.ValidationError({"task": "You have already reported this job."})
        return attrs


class ComplaintAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ("id", "status", "resolution_notes", "report_reason")
        read_only_fields = ("id", "report_reason")

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.status in (Complaint.Status.RESOLVED, Complaint.Status.DISMISSED):
            instance.resolved_by = self.context["request"].user
            instance.save(update_fields=["resolved_by", "updated_at"])
        return instance
