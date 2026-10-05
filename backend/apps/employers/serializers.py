from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import User
from apps.profiles.models import ClientProfile

from .models import EmployerVerification, VerificationDocument


class EmployerVerificationSerializer(serializers.ModelSerializer):
    employer_email = serializers.EmailField(source="employer.email", read_only=True)
    badge_text = serializers.ReadOnlyField()

    class Meta:
        model = EmployerVerification
        fields = (
            "id", "employer_email", "legal_name", "business_name", "employer_type", "business_address",
            "contact_phone", "recruiter_name", "website", "registration_number", "status", "applicant_notes",
            "admin_notes", "badge_text", "submitted_at", "reviewed_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "employer_email", "status", "admin_notes", "badge_text", "submitted_at", "reviewed_at", "created_at", "updated_at")

    def validate_employer_type(self, value):
        valid = {choice for choice, _ in ClientProfile.EmployerType.choices}
        if value not in valid:
            raise serializers.ValidationError("Choose a supported employer type.")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        return EmployerVerification.objects.create(employer=user, status=EmployerVerification.Status.PENDING, submitted_at=timezone.now(), **validated_data)

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.status = EmployerVerification.Status.PENDING
        instance.submitted_at = timezone.now()
        instance.reviewed_at = None
        instance.reviewed_by = None
        instance.admin_notes = ""
        instance.save()
        return instance


class VerificationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationDocument
        fields = ("id", "label", "file", "uploaded_at")
        read_only_fields = ("id", "uploaded_at")

    def validate_file(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Verification documents must be 5 MB or smaller.")
        content_type = getattr(value, "content_type", "")
        if content_type and content_type not in {"application/pdf", "image/png", "image/jpeg"}:
            raise serializers.ValidationError("Only PDF, PNG, and JPEG documents are accepted.")
        return value
