from django.utils import timezone
from rest_framework import serializers

from apps.profiles.models import ClientProfile
from apps.accounts.models import User
from apps.profiles.photo import profile_photo_url

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


class WorkerDirectorySerializer(serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    headline = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    experience_years = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    rating_average = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    reputation_score = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name", "headline", "bio", "location", "availability", "experience_years", "profile_photo", "skills", "rating_average", "rating_count", "reputation_score")

    def get_name(self, obj):
        return " ".join(part for part in (obj.first_name, obj.last_name) if part).strip() or "WorkNeuron worker"

    def get_profile_photo(self, obj):
        return profile_photo_url(obj, self.context.get("request"))

    def get_profile(self, obj):
        return getattr(obj, "worker_profile", None)

    def get_headline(self, obj):
        return getattr(self.get_profile(obj), "headline", "")

    def get_bio(self, obj):
        return getattr(self.get_profile(obj), "bio", "")

    def get_location(self, obj):
        return getattr(self.get_profile(obj), "location", "")

    def get_availability(self, obj):
        return getattr(self.get_profile(obj), "availability", "")

    def get_experience_years(self, obj):
        return getattr(self.get_profile(obj), "experience_years", 0)

    def get_skills(self, obj):
        return [{"id": item.skill_id, "name": item.skill.name, "proficiency": item.proficiency} for item in obj.worker_skills.all()]

    def get_rating_average(self, obj):
        return getattr(obj, "directory_rating_average", None)

    def get_rating_count(self, obj):
        return getattr(obj, "directory_rating_count", 0)

    def get_reputation_score(self, obj):
        return getattr(obj, "directory_reputation_score", 50)
