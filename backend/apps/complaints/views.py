from rest_framework import generics, permissions

from apps.accounts.models import User

from .models import Complaint
from .permissions import IsAdminRole
from .serializers import ComplaintAdminSerializer, ComplaintSerializer


class ComplaintListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "sensitive"

    def get_serializer_class(self):
        return ComplaintSerializer

    def get_queryset(self):
        queryset = Complaint.objects.select_related("complainant", "subject_user", "resolved_by")
        if self.request.user.role == User.Role.ADMIN:
            category = self.request.query_params.get("category")
            status = self.request.query_params.get("status")
            if category:
                queryset = queryset.filter(category=category)
            if status:
                queryset = queryset.filter(status=status)
            return queryset
        return queryset.filter(complainant=self.request.user)

    def perform_create(self, serializer):
        complaint = serializer.save(complainant=self.request.user)
        if complaint.category == Complaint.Category.JOB_REPORT:
            from apps.notifications.models import Notification
            from apps.notifications.services import create_notification
            for admin in User.objects.filter(role=User.Role.ADMIN, is_active=True):
                create_notification(admin, Notification.Kind.REPORT_RECEIVED, "Job report received", f"A report was submitted for {complaint.task.title}.", "/admin")


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
