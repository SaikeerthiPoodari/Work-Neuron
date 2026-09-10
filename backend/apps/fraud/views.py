from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from .models import FraudAlert
from .serializers import FraudAlertSerializer
from .services import scan_user


class IsAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN)


class FraudAlertListView(generics.ListAPIView):
    serializer_class = FraudAlertSerializer
    permission_classes = [IsAdminOnly]
    queryset = FraudAlert.objects.select_related("user")


class FraudScanView(APIView):
    permission_classes = [IsAdminOnly]

    def post(self, request):
        user = get_object_or_404(User, pk=request.data.get("user_id"))
        alerts = scan_user(user)
        return Response(FraudAlertSerializer(alerts, many=True).data, status=status.HTTP_200_OK)


class FraudAlertDetailView(generics.UpdateAPIView):
    queryset = FraudAlert.objects.select_related("user")
    serializer_class = FraudAlertSerializer
    permission_classes = [IsAdminOnly]

