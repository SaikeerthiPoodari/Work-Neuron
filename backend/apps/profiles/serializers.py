from rest_framework import serializers
from django.conf import settings
from uuid import uuid4

from .models import ClientProfile, ProfessionalPortfolio, WorkerProfile
from .languages import LANGUAGES


class ClientProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    profile_completion = serializers.SerializerMethodField()

    class Meta:
        model = ClientProfile
        fields = ("id", "email", "organization_name", "bio", "phone", "location", "website", "profile_photo", "cover_image", "employer_type", "bank_account_name", "bank_name", "bank_account_number", "bank_account_type", "bank_ifsc", "upi_id", "profile_completion", "updated_at")
        read_only_fields = ("id", "email", "updated_at")

    def validate_profile_photo(self, image):
        if image and image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Photo must be 5 MB or smaller.")
        return image

    def validate_cover_image(self, image):
        if image and image.size > 8 * 1024 * 1024:
            raise serializers.ValidationError("Cover image must be 8 MB or smaller.")
        return image

    def get_profile_completion(self, obj):
        fields = [obj.organization_name, obj.bio, obj.location, obj.website, obj.employer_type, obj.profile_photo, obj.cover_image]
        return round(sum(bool(value) for value in fields) * 100 / len(fields))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.profile_photo:
            request = self.context.get("request")
            url = instance.profile_photo.url
            data["profile_photo"] = request.build_absolute_uri(url) if request else url
        else:
            data["profile_photo"] = ""
        if instance.cover_image:
            request = self.context.get("request")
            url = instance.cover_image.url
            data["cover_image"] = request.build_absolute_uri(url) if request else url
        else:
            data["cover_image"] = ""
        return data


class WorkerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    languages = serializers.ListField(child=serializers.ChoiceField(choices=LANGUAGES), required=False)
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    profile_completion = serializers.SerializerMethodField()

    class Meta:
        model = WorkerProfile
        fields = (
            "id", "email", "headline", "bio", "experience_years", "location",
            "availability", "portfolio_url", "profile_photo_url", "profile_photo", "cover_image", "education", "interests", "languages", "preferred_job_type", "preferred_salary",
            "preferred_working_hours", "profile_completion", "updated_at",
            "current_city", "current_area", "current_state", "latitude", "longitude", "preferred_radius_km",
            "preferred_job_location", "remote_preference", "bank_account_name", "bank_name", "bank_account_number", "bank_account_type", "bank_ifsc", "upi_id", "payout_qr_token",
        )
        read_only_fields = ("id", "email", "updated_at")

    def validate_profile_photo(self, image):
        if image and image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Photo must be 5 MB or smaller.")
        return image

    def get_profile_completion(self, obj):
        fields = [obj.headline, obj.bio, obj.experience_years, obj.location, obj.education, obj.interests, obj.languages, obj.profile_photo or obj.profile_photo_url, obj.cover_image, obj.availability]
        skill_bonus = 1 if obj.user.worker_skills.exists() else 0
        return round((sum(bool(value) for value in fields) + skill_bonus) * 100 / (len(fields) + 1))

    def validate_cover_image(self, image):
        if image and image.size > 8 * 1024 * 1024:
            raise serializers.ValidationError("Cover image must be 8 MB or smaller.")
        return image

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.profile_photo:
            request = self.context.get("request")
            url = instance.profile_photo.url
            data["profile_photo"] = request.build_absolute_uri(url) if request else url
        else:
            data["profile_photo"] = ""
        if instance.cover_image:
            request = self.context.get("request")
            url = instance.cover_image.url
            data["cover_image"] = request.build_absolute_uri(url) if request else url
        else:
            data["cover_image"] = ""
        return data

    def validate(self, attrs):
        latitude = attrs.get("latitude", getattr(self.instance, "latitude", None))
        longitude = attrs.get("longitude", getattr(self.instance, "longitude", None))
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError("Latitude and longitude must be provided together, or both cleared.")
        return attrs

    def validate_languages(self, value):
        return list(dict.fromkeys(value))

    def create(self, validated_data):
        validated_data.setdefault("payout_qr_token", f"WN-{uuid4().hex}")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.setdefault("payout_qr_token", instance.payout_qr_token or f"WN-{uuid4().hex}")
        return super().update(instance, validated_data)


class ProfessionalPortfolioSerializer(serializers.ModelSerializer):
    worker = serializers.IntegerField(source="worker_id", read_only=True)
    worker_name = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    performance = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()

    class Meta:
        model = ProfessionalPortfolio
        fields = ("worker", "worker_name", "profile", "summary", "experience", "skills", "performance", "reviews", "achievements", "generated_at", "source_assignment_count", "updated_at")
        read_only_fields = fields

    def get_worker_name(self, obj):
        return " ".join(filter(None, [obj.worker.first_name, obj.worker.last_name])) or obj.worker.email

    def get_profile(self, obj):
        profile = getattr(obj.worker, "worker_profile", None)
        if not profile:
            return {}
        request = self.context.get("request")
        photo = ""
        if profile.profile_photo:
            photo = request.build_absolute_uri(profile.profile_photo.url) if request else profile.profile_photo.url
        return {"headline": profile.headline, "bio": profile.bio, "location": profile.location, "education": profile.education, "profile_photo": photo or profile.profile_photo_url, "experience_years": profile.experience_years}

    def get_experience(self, obj):
        from apps.assignments.models import Assignment
        items = Assignment.objects.filter(worker=obj.worker, task__status="COMPLETED").select_related("task__owner", "task__owner__client_profile").prefetch_related("task__skills").order_by("-completed_at", "-id")
        result = []
        for item in items:
            owner = item.task.owner
            client_profile = getattr(owner, "client_profile", None)
            client_name = (client_profile.organization_name if client_profile and client_profile.organization_name else " ".join(filter(None, [owner.first_name, owner.last_name])) or "WorkNeuron client")
            result.append({"assignment_id": item.id, "title": item.task.title, "client_name": client_name, "started_at": item.started_at, "completed_at": item.completed_at, "duration_days": (item.completed_at.date() - item.started_at.date()).days if item.started_at and item.completed_at else None, "description": item.task.description, "category": item.task.category, "skills": [skill.name for skill in item.task.skills.all()]})
        return result

    def get_skills(self, obj):
        return [{"name": item.skill.name, "category": item.skill.category, "proficiency": item.proficiency, "years_experience": item.years_experience} for item in obj.worker.worker_skills.select_related("skill").all()]

    def get_performance(self, obj):
        from django.db.models import Avg, Count
        from apps.reviews.models import Review
        reviews = Review.objects.filter(reviewed_user=obj.worker, reviewer__role="CLIENT", assignment__task__status="COMPLETED")
        result = reviews.aggregate(average=Avg("rating"), count=Count("id"))
        return {"completed_assignments": obj.source_assignment_count, "average_rating": round(float(result["average"]), 2) if result["average"] is not None else None, "review_count": result["count"] or 0}

    def get_reviews(self, obj):
        from apps.reviews.models import Review
        return [{"rating": item.rating, "review": item.review, "client_name": (getattr(item.reviewer, "client_profile", None).organization_name if getattr(item.reviewer, "client_profile", None) and getattr(item.reviewer, "client_profile", None).organization_name else " ".join(filter(None, [item.reviewer.first_name, item.reviewer.last_name])) or "WorkNeuron client"), "created_at": item.created_at} for item in Review.objects.filter(reviewed_user=obj.worker, reviewer__role="CLIENT", assignment__task__status="COMPLETED").select_related("reviewer", "reviewer__client_profile").order_by("-created_at", "-id")]

    def get_achievements(self, obj):
        achievements = []
        if obj.source_assignment_count:
            achievements.append({"key": "completed_assignments", "label": f"{obj.source_assignment_count} verified assignment{'s' if obj.source_assignment_count != 1 else ''} completed", "verified": True})
        performance = self.get_performance(obj)
        if performance["average_rating"] is not None:
            achievements.append({"key": "client_rating", "label": f"{performance['average_rating']}/5 verified client rating", "verified": True})
        return achievements
