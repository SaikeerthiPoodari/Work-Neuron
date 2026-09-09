from rest_framework import serializers

from apps.accounts.serializers import UserSerializer


class WorkerMatchSerializer(serializers.Serializer):
    worker = UserSerializer(read_only=True)
    match = serializers.DictField()


class TaskRecommendationSerializer(serializers.Serializer):
    task = serializers.DictField()
    match = serializers.DictField()

