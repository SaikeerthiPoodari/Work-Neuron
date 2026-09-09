from rest_framework import serializers


class RecommendationSerializer(serializers.Serializer):
    task = serializers.DictField()
    match = serializers.DictField()

