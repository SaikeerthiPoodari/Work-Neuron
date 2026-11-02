from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import respond


class AssistantRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, trim_whitespace=True)
    context = serializers.JSONField(required=False, default=dict)
    media = serializers.ListField(child=serializers.DictField(), required=False, allow_empty=True, max_length=3)


class AssistantView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "sensitive"

    def post(self, request):
        serializer = AssistantRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        context = serializer.validated_data["context"]
        media = []
        for item in serializer.validated_data.get("media", []):
            media_type = str(item.get("type", ""))[:80]
            data = str(item.get("data", ""))
            if media_type.startswith("image/") and data.startswith("data:image/") and len(data) <= 4_000_000:
                media.append({"name": str(item.get("name", "image"))[:120], "type": media_type, "data": data})
        # Never trust a client-supplied role: role comes from the JWT-authenticated user.
        history = context.get("history", []) if isinstance(context.get("history", []), list) else []
        safe_context = {
            "page": str(context.get("page", ""))[:200],
            "entity_id": str(context.get("entity_id", ""))[:64],
            "role": request.user.role,
            "language": str(context.get("language", "auto"))[:12],
            "history": [{"role": item.get("role", "user"), "content": str(item.get("content", ""))[:1000]} for item in history[-8:] if isinstance(item, dict)],
        }
        return Response(respond(request.user, serializer.validated_data["message"], safe_context, media=media), status=status.HTTP_200_OK)
