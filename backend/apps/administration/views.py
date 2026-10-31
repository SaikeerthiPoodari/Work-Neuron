from django.db.models import Q
from rest_framework import generics

from apps.accounts.models import User
from apps.applications.models import Application
from apps.applications.serializers import ApplicationSerializer
from apps.assignments.models import Assignment
from apps.assignments.serializers import AssignmentSerializer
from apps.complaints.models import Complaint
from apps.complaints.serializers import ComplaintSerializer
from apps.fraud.models import FraudAlert
from apps.fraud.serializers import FraudAlertSerializer
from apps.payments.models import Transaction
from apps.payments.serializers import TransactionSerializer
from apps.tasks.models import Task
from apps.tasks.serializers import TaskSerializer

from .permissions import IsAdminRole
from .models import AuditEvent, record_audit_event
from .serializers import AdminUserSerializer, AuditEventSerializer


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        queryset = User.objects.all()
        search = self.request.query_params.get("search", "").strip()
        role = self.request.query_params.get("role", "").strip().upper()
        active = self.request.query_params.get("active")
        if search:
            queryset = queryset.filter(Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search))
        if role in User.Role.values:
            queryset = queryset.filter(role=role)
        if active in {"true", "false"}:
            queryset = queryset.filter(is_active=active == "true")
        return queryset


class AdminUserDetailView(generics.UpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()

    def perform_update(self, serializer):
        if serializer.instance == self.request.user and serializer.validated_data.get("is_active") is False:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"is_active": "You cannot deactivate your own administrator account."})
        before = {field: getattr(serializer.instance, field) for field in ("is_active", "role", "is_staff")}
        user = serializer.save()
        changed = {field: {"from": before[field], "to": getattr(user, field)} for field in before if before[field] != getattr(user, field)}
        if changed:
            record_audit_event(self.request, "USER_ACCOUNT_UPDATED", user, changed)


class AdminAuditEventListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        queryset = AuditEvent.objects.select_related("actor")
        action = self.request.query_params.get("action", "").strip()
        if action:
            queryset = queryset.filter(action=action)
        return queryset[:200]


class AdminTaskListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = TaskSerializer
    queryset = Task.objects.select_related("owner").prefetch_related("skills")


class AdminApplicationListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = ApplicationSerializer
    queryset = Application.objects.select_related("task", "worker")


class AdminAssignmentListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AssignmentSerializer
    queryset = Assignment.objects.select_related("task", "worker", "application")


class AdminTransactionListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.select_related("assignment__task", "payer")


class AdminComplaintListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = ComplaintSerializer
    queryset = Complaint.objects.select_related("complainant", "subject_user", "resolved_by")


class AdminFraudAlertListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = FraudAlertSerializer
    queryset = FraudAlert.objects.select_related("user")

