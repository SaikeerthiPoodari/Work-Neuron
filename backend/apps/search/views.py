from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SearchEvent
from .serializers import VoiceSearchSerializer
from .services import parse_voice_query


class VoiceSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "sensitive"

    def post(self, request):
        serializer = VoiceSearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = parse_voice_query(serializer.validated_data["recognized_text"])
        SearchEvent.objects.create(user=request.user, kind=SearchEvent.Kind.VOICE, language=result["language"], confidence=result["confidence"])
        return Response(result)
