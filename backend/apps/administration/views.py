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
from .serializers import AdminUserSerializer


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()


class AdminUserDetailView(generics.UpdateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()

    def perform_update(self, serializer):
        if serializer.instance == self.request.user and serializer.validated_data.get("is_active") is False:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"is_active": "You cannot deactivate your own administrator account."})
        serializer.save()


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

