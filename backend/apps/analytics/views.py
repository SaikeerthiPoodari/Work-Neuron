from django.db.models import Sum
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment
from apps.complaints.models import Complaint
from apps.fraud.models import FraudAlert
from apps.payments.models import Transaction
from apps.reviews.models import Review
from apps.tasks.models import Task


class AnalyticsSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "Administrator privileges are required."}, status=403)
        return Response({
            "users": {
                "total": User.objects.count(),
                "active": User.objects.filter(is_active=True).count(),
                "clients": User.objects.filter(role=User.Role.CLIENT).count(),
                "workers": User.objects.filter(role=User.Role.WORKER).count(),
                "admins": User.objects.filter(role=User.Role.ADMIN).count(),
            },
            "tasks": {"total": Task.objects.count(), "by_status": {status: Task.objects.filter(status=status).count() for status, _ in Task.Status.choices}},
            "applications": {"total": Application.objects.count(), "submitted": Application.objects.filter(status=Application.Status.SUBMITTED).count()},
            "assignments": {"total": Assignment.objects.count(), "completed": Assignment.objects.filter(task__status=Task.Status.COMPLETED).count()},
            "transactions": {
                "total": Transaction.objects.count(),
                "verified": Transaction.objects.filter(status=Transaction.Status.VERIFIED).count(),
                "verified_amount": str(Transaction.objects.filter(status=Transaction.Status.VERIFIED).aggregate(total=Sum("amount"))["total"] or 0),
            },
            "reviews": Review.objects.count(),
            "complaints": {"total": Complaint.objects.count(), "open": Complaint.objects.filter(status=Complaint.Status.OPEN).count()},
            "fraud_alerts": {"total": FraudAlert.objects.count(), "open": FraudAlert.objects.filter(status=FraudAlert.Status.OPEN).count()},
        })

