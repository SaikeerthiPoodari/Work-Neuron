from rest_framework import generics, permissions

from apps.accounts.models import User

from .models import Complaint
from .permissions import IsAdminRole
from .serializers import ComplaintAdminSerializer, ComplaintSerializer


class ComplaintListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return ComplaintSerializer

    def get_queryset(self):
        queryset = Complaint.objects.select_related("complainant", "subject_user", "resolved_by")
        if self.request.user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(complainant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(complainant=self.request.user)


class ComplaintDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Complaint.objects.select_related("complainant", "subject_user", "resolved_by")
        if self.request.user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(complainant=self.request.user)

    def get_serializer_class(self):
        if self.request.user.role == User.Role.ADMIN and self.request.method in ("PATCH", "PUT"):
            return ComplaintAdminSerializer
        return ComplaintSerializer

