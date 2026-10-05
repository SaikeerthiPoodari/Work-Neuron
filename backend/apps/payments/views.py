import hashlib
import hmac
import json
import os

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.tasks.models import Task

from .models import Transaction
from .serializers import PaymentVerifySerializer, TransactionSerializer
from .services import PaymentConfigurationError, create_test_order, verify_test_payment


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.select_related("assignment__task", "payer")
        if self.request.user.role == User.Role.ADMIN:
            return queryset
        if self.request.user.role == User.Role.CLIENT:
            return queryset.filter(assignment__task__owner=self.request.user)
        return queryset.filter(assignment__worker=self.request.user)


class EmployerDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in (User.Role.CLIENT, User.Role.ADMIN):
            return Response({"detail": "Only employers or administrators can view employer financials."}, status=status.HTTP_403_FORBIDDEN)
        assignments = Assignment.objects.select_related("task", "worker").filter(task__owner=request.user)
        transactions = Transaction.objects.select_related("assignment__task", "assignment__worker").filter(assignment__task__owner=request.user)
        verified = transactions.filter(status=Transaction.Status.VERIFIED)
        completed = assignments.filter(task__status=Task.Status.COMPLETED)
        active_tasks = Task.objects.filter(owner=request.user).exclude(status__in=[Task.Status.COMPLETED, Task.Status.CANCELLED]).prefetch_related("applications")
        from apps.applications.models import Application
        applications = Application.objects.filter(task__owner=request.user)
        from apps.complaints.models import Complaint
        reports = Complaint.objects.filter(task__owner=request.user)
        verification = getattr(request.user, "employer_verification", None)
        money = lambda value: f"{value or 0:.2f}"
        return Response({
            "summary": {
                "total_earnings": money(verified.aggregate(total=Sum("amount"))["total"]),
                "completed_job_earnings": money(verified.filter(assignment__task__status=Task.Status.COMPLETED).aggregate(total=Sum("amount"))["total"]),
                "pending_payments": money(transactions.exclude(status__in=[Transaction.Status.VERIFIED, Transaction.Status.REFUNDED]).aggregate(total=Sum("amount"))["total"]),
            },
            "completed_jobs": [{
                "assignment_id": item.id, "job_title": item.task.title, "worker": item.worker.email,
                "completion_date": item.completed_at, "amount": str(item.task.budget), "status": item.task.status,
            } for item in completed],
            "active_jobs": [{"id": item.id, "title": item.title, "status": item.status, "applications": item.applications.count()} for item in active_tasks],
            "application_count": applications.count(),
            "selected_worker_count": applications.filter(status=Application.Status.ACCEPTED).values("worker_id").distinct().count(),
            "report_count": reports.count(),
            "verification": {"status": verification.status, "badge_text": verification.badge_text} if verification else {"status": "UNVERIFIED", "badge_text": ""},
            "payment_history": TransactionSerializer(transactions, many=True).data,
        })


class PaymentCreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "sensitive"

    def post(self, request):
        if request.user.role != User.Role.CLIENT:
            return Response({"detail": "Only clients can create payment orders."}, status=status.HTTP_403_FORBIDDEN)
        assignment = get_object_or_404(Assignment.objects.select_related("task"), pk=request.data.get("assignment"))
        if assignment.task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner can create its payment."}, status=status.HTTP_403_FORBIDDEN)
        try:
            transaction, order = create_test_order(assignment, request.user)
        except PaymentConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "transaction": TransactionSerializer(transaction).data,
            "order": order,
            "key_id": __import__("os").getenv("RAZORPAY_KEY_ID"),
            "test_mode": True,
        }, status=status.HTTP_201_CREATED if order else status.HTTP_200_OK)


class PaymentVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "sensitive"

    def post(self, request):
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = get_object_or_404(Transaction.objects.select_related("assignment__task"), pk=serializer.validated_data["transaction_id"])
        if request.user.role != User.Role.ADMIN and transaction.assignment.task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner or an administrator can verify this payment."}, status=status.HTTP_403_FORBIDDEN)
        try:
            transaction = verify_test_payment(
                transaction,
                serializer.validated_data["razorpay_order_id"],
                serializer.validated_data["razorpay_payment_id"],
                serializer.validated_data["razorpay_signature"],
            )
        except Exception as exc:
            if isinstance(exc, DjangoValidationError):
                detail = exc.messages[0]
            else:
                detail = str(exc)
            transaction.status = Transaction.Status.FAILED
            transaction.save(update_fields=["status", "updated_at"])
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(transaction.assignment.worker, Notification.Kind.PAYMENT_UPDATE, "Payment verified", f"Payment for {transaction.assignment.task.title} was verified.", f"/payments/{transaction.id}")
        return Response(TransactionSerializer(transaction).data)


class RazorpayWebhookView(APIView):
    """Verify Razorpay webhook signatures and apply idempotent payment state updates."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_scope = "sensitive"

    def post(self, request):
        secret = os.getenv("RAZORPAY_WEBHOOK_SECRET") or os.getenv("RAZORPAY_KEY_SECRET")
        supplied = request.headers.get("X-Razorpay-Signature", "")
        if not secret or not supplied:
            return Response({"detail": "Webhook signature is not configured."}, status=status.HTTP_401_UNAUTHORIZED)
        expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied):
            return Response({"detail": "Invalid webhook signature."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            payload = json.loads(request.body.decode("utf-8"))
            event = payload.get("event", "")
            entity = payload["payload"]["payment"]["entity"]
            order_id = entity.get("order_id")
            payment_id = entity.get("id")
        except (ValueError, KeyError, TypeError):
            return Response({"detail": "Invalid webhook payload."}, status=status.HTTP_400_BAD_REQUEST)
        transaction = Transaction.objects.filter(provider_order_id=order_id).first()
        if transaction is None:
            return Response({"received": True, "matched": False})
        if event in {"payment.captured", "payment.authorized"}:
            transaction.status = Transaction.Status.VERIFIED
            transaction.provider_payment_id = payment_id or transaction.provider_payment_id
        elif event == "payment.failed":
            transaction.status = Transaction.Status.FAILED
        transaction.save(update_fields=["status", "provider_payment_id", "updated_at"])
        return Response({"received": True, "matched": True, "status": transaction.status})
