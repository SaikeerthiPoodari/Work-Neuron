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
        if request and request.user.is_authenticated and request.user.role != "ADMIN":
            assignment = attrs.get("assignment")
            application = attrs.get("application")
            transaction = attrs.get("transaction")
            task = attrs.get("task")
            subject = attrs.get("subject_user")
            if assignment and assignment.worker_id != request.user.id and assignment.task.owner_id != request.user.id:
                raise serializers.ValidationError({"assignment": "You are not a participant in this assignment."})
            if application and application.worker_id != request.user.id and application.task.owner_id != request.user.id:
                raise serializers.ValidationError({"application": "You are not a participant in this application."})
            if transaction and transaction.assignment.worker_id != request.user.id and transaction.assignment.task.owner_id != request.user.id:
                raise serializers.ValidationError({"transaction": "You are not a participant in this transaction."})
            if task and task.owner_id != request.user.id and not assignment and not application:
                # Reporting another person's task is allowed only through the dedicated report category.
                if category != Complaint.Category.JOB_REPORT:
                    raise serializers.ValidationError({"task": "Choose one of your own tasks or report the job with the job report category."})
            if subject and subject.id != request.user.id and not assignment and not application:
                raise serializers.ValidationError({"subject_user": "Choose a user connected to your assignment or application."})
        if request and category == Complaint.Category.JOB_REPORT and task and task.owner_id == request.user.id:
            raise serializers.ValidationError({"task": "You cannot report your own job."})
        if category != Complaint.Category.SUPPORT and not any(attrs.get(field) for field in ("subject_user", "task", "application", "assignment", "transaction")):
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
