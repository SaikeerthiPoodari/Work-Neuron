from rest_framework import serializers


class VoiceSearchSerializer(serializers.Serializer):
    recognized_text = serializers.CharField(max_length=500, allow_blank=False, trim_whitespace=True)
