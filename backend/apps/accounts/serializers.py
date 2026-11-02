from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User
from apps.profiles.models import ClientProfile, WorkerProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role", "preferred_language", "date_joined")
        read_only_fields = ("id", "date_joined", "role", "email")


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        if not self.context["request"].user.check_password(attrs["current_password"]):
            raise serializers.ValidationError({"current_password": "Current password is incorrect."})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    organization_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    employer_type = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("email", "password", "password_confirm", "first_name", "last_name", "role", "phone", "organization_name", "employer_type")

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Administrator accounts cannot be self-registered.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        profile_data = {key: validated_data.pop(key, "") for key in ("phone", "organization_name", "employer_type")}
        user = User.objects.create_user(**validated_data)
        if user.role == User.Role.CLIENT:
            ClientProfile.objects.create(user=user, **profile_data)
        else:
            WorkerProfile.objects.create(user=user)
        return user


class WorkNeuronTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.ChoiceField(choices=User.Role.choices, required=False, write_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        requested_role = attrs.get("role")
        data = super().validate(attrs)
        if requested_role and requested_role != self.user.role:
            labels = {User.Role.WORKER: "Worker", User.Role.CLIENT: "Client", User.Role.ADMIN: "Admin"}
            raise serializers.ValidationError(
                {"role": f"This account is registered as a {labels[self.user.role]}. Please use {labels[self.user.role]} Login."}
            )
        data["user"] = UserSerializer(self.user).data
        return data

