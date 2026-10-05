from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import respond


class AssistantRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, trim_whitespace=True)
    context = serializers.JSONField(required=False, default=dict)


class AssistantView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "sensitive"

    def post(self, request):
        serializer = AssistantRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        context = serializer.validated_data["context"]
        # Never trust a client-supplied role: role comes from the JWT-authenticated user.
        safe_context = {"page": str(context.get("page", ""))[:200], "entity_id": str(context.get("entity_id", ""))[:64], "role": request.user.role}
        return Response(respond(request.user, serializer.validated_data["message"], safe_context), status=status.HTTP_200_OK)
