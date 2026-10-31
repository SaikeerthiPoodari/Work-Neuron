from rest_framework import serializers

from .models import Assignment, AssignmentLevel, AssignmentLevelTask


class AssignmentLevelTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentLevelTask
        fields = ("id", "title", "is_completed", "completed_at", "client_completed", "client_completed_at")


class AssignmentLevelSerializer(serializers.ModelSerializer):
    tasks = AssignmentLevelTaskSerializer(source="checklist_items", many=True, read_only=True)
    class Meta:
        model = AssignmentLevel
        fields = ("id", "order", "title", "description", "requirements", "expected_completion_date", "payment_amount", "status", "submission", "feedback", "submitted_at", "reviewed_at", "tasks")
        read_only_fields = ("id", "status", "submission", "feedback", "submitted_at", "reviewed_at")


class AssignmentLevelInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=180)
    description = serializers.CharField(required=False, allow_blank=True)
    requirements = serializers.CharField(required=False, allow_blank=True)
    expected_completion_date = serializers.DateField(required=False, allow_null=True)
    payment_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False, default=None, allow_null=True)
    tasks = serializers.ListField(child=serializers.CharField(max_length=240, trim_whitespace=True), required=False, allow_empty=True, max_length=30)


class AssignmentLevelsConfigSerializer(serializers.Serializer):
    levels = AssignmentLevelInputSerializer(many=True, min_length=1, max_length=30)


class LevelSubmissionSerializer(serializers.Serializer):
    submission = serializers.CharField(allow_blank=False, trim_whitespace=True)


class LevelReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("approve", "changes"))
    feedback = serializers.CharField(required=False, allow_blank=True)


class AssignmentSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="task.title", read_only=True)
    task_description = serializers.CharField(source="task.description", read_only=True)
    task_deadline = serializers.DateTimeField(source="task.deadline", read_only=True)
    task_start_date = serializers.DateField(source="task.start_date", read_only=True)
    task_end_date = serializers.DateField(source="task.end_date", read_only=True)
    worker_email = serializers.EmailField(source="worker.email", read_only=True)
    client_name = serializers.SerializerMethodField()
    task_status = serializers.CharField(source="task.status", read_only=True)
    levels = AssignmentLevelSerializer(many=True, read_only=True)
    current_level = serializers.SerializerMethodField()
    worker_name = serializers.SerializerMethodField()
    worker_headline = serializers.SerializerMethodField()
    worker_location = serializers.SerializerMethodField()
    worker_profile_photo = serializers.SerializerMethodField()
    application_created_at = serializers.DateTimeField(source="application.created_at", read_only=True)
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = (
            "id", "task", "task_title", "task_description", "task_deadline", "task_start_date", "task_end_date", "task_status", "worker_email", "worker_name", "client_name", "worker_headline", "worker_location", "worker_profile_photo", "application", "application_created_at", "progress", "submission",
            "client_feedback", "started_at", "worker_started_at", "client_started_at", "submitted_at", "completed_at", "created_at", "updated_at", "levels", "current_level", "payment",
        )
        read_only_fields = (
            "id", "task", "task_title", "task_description", "task_deadline", "task_start_date", "task_end_date", "task_status", "worker_email", "worker_name", "client_name", "worker_headline", "worker_location", "worker_profile_photo", "application", "application_created_at", "progress", "submission",
            "client_feedback", "started_at", "worker_started_at", "client_started_at", "submitted_at", "completed_at", "created_at", "updated_at", "levels", "current_level", "payment",
        )

    def get_current_level(self, obj):
        level = next((item for item in obj.levels.all() if item.status in (AssignmentLevel.Status.CURRENT, AssignmentLevel.Status.SUBMITTED)), None)
        return AssignmentLevelSerializer(level).data if level else None

    def get_worker_name(self, obj):
        return " ".join(filter(None, [obj.worker.first_name, obj.worker.last_name])) or obj.worker.email

    def get_client_name(self, obj):
        owner = obj.task.owner
        return " ".join(filter(None, [owner.first_name, owner.last_name])) or owner.email

    def get_worker_headline(self, obj):
        return getattr(getattr(obj.worker, "worker_profile", None), "headline", "")

    def get_worker_location(self, obj):
        profile = getattr(obj.worker, "worker_profile", None)
        return getattr(profile, "location", "") if profile else ""

    def get_worker_profile_photo(self, obj):
        profile = getattr(obj.worker, "worker_profile", None)
        if not profile:
            return ""
        photo = profile.profile_photo
        if photo:
            request = self.context.get("request")
            return request.build_absolute_uri(photo.url) if request else photo.url
        return profile.profile_photo_url

    def get_payment(self, obj):
        transaction = obj.transactions.order_by("-created_at").first()
        if not transaction:
            return {"status": "NOT_CREATED", "amount": None, "currency": "INR"}
        return {"status": transaction.status, "escrow_status": transaction.escrow_status, "amount": str(transaction.amount), "currency": transaction.currency, "transaction_id": transaction.id, "updated_at": transaction.updated_at}


class ProgressSerializer(serializers.Serializer):
    progress = serializers.IntegerField(min_value=0, max_value=100)


class SubmissionSerializer(serializers.Serializer):
    submission = serializers.CharField(allow_blank=False, trim_whitespace=True)


class CompletionSerializer(serializers.Serializer):
    client_feedback = serializers.CharField(required=False, allow_blank=True)
