import hashlib
import hmac
import json
import os
import re
import secrets

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from datetime import timedelta
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.tasks.models import Task

from .models import BankAccount, PaymentMethod, PaymentProfile, PayoutRecord, Transaction
from .serializers import BankAccountSerializer, PaymentMethodSerializer, PaymentProfileSerializer, PaymentVerifySerializer, PayoutRecordSerializer, TransactionSerializer
from .services import PaymentConfigurationError, create_test_order, refund_test_payment, verify_test_payment


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


def get_payment_profile(user):
    profile, _ = PaymentProfile.objects.get_or_create(user=user, defaults={"qr_token": f"WN-{secrets.token_urlsafe(32)}"})
    if not profile.qr_token:
        profile.qr_token = f"WN-{secrets.token_urlsafe(32)}"
        profile.save(update_fields=["qr_token", "updated_at"])
    return profile


class WalletOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        transactions = Transaction.objects.filter(assignment__worker=request.user) if request.user.role == User.Role.WORKER else Transaction.objects.filter(assignment__task__owner=request.user)
        verified = transactions.filter(status=Transaction.Status.VERIFIED)
        held = verified.filter(escrow_status=Transaction.EscrowStatus.HELD)
        released = verified.filter(escrow_status=Transaction.EscrowStatus.RELEASED)
        refunded = transactions.filter(status=Transaction.Status.REFUNDED)
        total = lambda qs: str(qs.aggregate(value=Sum("amount"))["value"] or 0)
        return Response({"role": request.user.role, "profile": PaymentProfileSerializer(get_payment_profile(request.user), context={"request": request}).data, "summary": {"total": total(verified), "held": total(held), "released": total(released), "refunded": total(refunded), "pending": total(transactions.filter(status=Transaction.Status.CREATED))}, "transactions": TransactionSerializer(transactions.select_related("assignment__task", "assignment__task__owner"), many=True).data, "bank_accounts": BankAccountSerializer(BankAccount.objects.filter(user=request.user), many=True).data, "payment_methods": PaymentMethodSerializer(PaymentMethod.objects.filter(user=request.user), many=True).data, "payouts": PayoutRecordSerializer(PayoutRecord.objects.filter(worker=request.user).select_related("transaction__assignment__task"), many=True).data})


class BankAccountListCreateView(generics.ListCreateAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        account = serializer.save(user=self.request.user, verification_status=BankAccount.VerificationStatus.PENDING)
        if not BankAccount.objects.filter(user=self.request.user).exclude(pk=account.pk).exists() or account.is_primary:
            BankAccount.objects.filter(user=self.request.user).exclude(pk=account.pk).update(is_primary=False)
            account.is_primary = True
            account.save(update_fields=["is_primary", "updated_at"])


class BankAccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BankAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankAccount.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        account = serializer.save(verification_status=BankAccount.VerificationStatus.PENDING)
        if account.is_primary:
            BankAccount.objects.filter(user=self.request.user).exclude(pk=account.pk).update(is_primary=False)

    def perform_destroy(self, instance):
        if instance.payouts.filter(status=PayoutRecord.Status.PROCESSING).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("This account cannot be removed while a payout is processing.")
        instance.delete()


class PaymentMethodListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        method = serializer.save(user=self.request.user, verification_status="PENDING")
        if method.is_primary:
            PaymentMethod.objects.filter(user=self.request.user).exclude(pk=method.pk).update(is_primary=False)


class PaymentPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = get_payment_profile(request.user)
        current = request.data.get("current_pin", "")
        new_pin = str(request.data.get("new_pin", ""))
        confirm = str(request.data.get("confirm_pin", ""))
        if not re.fullmatch(r"\d{6}", new_pin) or new_pin != confirm:
            return Response({"detail": "Payment PIN must be six matching digits."}, status=status.HTTP_400_BAD_REQUEST)
        if profile.pin_hash and not check_password(current, profile.pin_hash):
            profile.pin_attempts += 1
            profile.save(update_fields=["pin_attempts", "updated_at"])
            return Response({"detail": "Current payment PIN is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
        profile.pin_hash = make_password(new_pin)
        profile.pin_attempts = 0
        profile.pin_locked_until = None
        profile.save(update_fields=["pin_hash", "pin_attempts", "pin_locked_until", "updated_at"])
        return Response({"detail": "Payment PIN saved securely."})


class PaymentQrView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(PaymentProfileSerializer(get_payment_profile(request.user), context={"request": request}).data)

    def post(self, request):
        profile = get_payment_profile(request.user)
        profile.qr_token = f"WN-{secrets.token_urlsafe(32)}"
        profile.qr_revoked = False
        profile.save(update_fields=["qr_token", "qr_revoked", "updated_at"])
        return Response(PaymentProfileSerializer(profile, context={"request": request}).data)


class PaymentQrResolveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, token):
        profile = get_object_or_404(PaymentProfile.objects.select_related("user"), qr_token=token, qr_revoked=False)
        user = profile.user
        return Response({"workneuron_id": user.id, "name": " ".join(filter(None, [user.first_name, user.last_name])) or user.email, "role": user.role, "email": user.email if request.user.role == User.Role.ADMIN else None, "profile_id": profile.id, "payment_profile_verified": True})


class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Transaction.objects.select_related("assignment__task", "payer")
        if self.request.user.role == User.Role.ADMIN:
            return queryset
        if self.request.user.role == User.Role.CLIENT:
            return queryset.filter(assignment__task__owner=self.request.user)
        return queryset.filter(assignment__worker=self.request.user)


class PaymentAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        queryset = Transaction.objects.filter(status__in=[Transaction.Status.VERIFIED, Transaction.Status.CREATED]).select_related("assignment__task")
        if request.user.role == User.Role.WORKER:
            queryset = queryset.filter(assignment__worker=request.user)
        elif request.user.role == User.Role.CLIENT:
            queryset = queryset.filter(assignment__task__owner=request.user)
        else:
            queryset = queryset
        range_name = request.query_params.get("range", "6m")
        days = {"7d": 7, "30d": 30, "3m": 90, "6m": 180}.get(range_name)
        if days:
            queryset = queryset.filter(created_at__gte=timezone.now() - timedelta(days=days))
        verified = queryset.filter(status=Transaction.Status.VERIFIED)
        money = lambda value: f"{value or 0:.2f}"
        status_totals = list(queryset.values("status").annotate(total=Sum("amount"), count=Count("id")))
        monthly = list(verified.annotate(period=TruncMonth("created_at")).values("period").annotate(total=Sum("amount"), count=Count("id")).order_by("period"))
        daily = list(verified.annotate(period=TruncDate("created_at")).values("period").annotate(total=Sum("amount"), count=Count("id")).order_by("period"))
        return Response({
            "range": range_name,
            "currency": "INR",
            "summary": {"total_earnings": money(verified.aggregate(total=Sum("amount"))["total"]), "pending_payments": money(queryset.filter(status=Transaction.Status.CREATED).aggregate(total=Sum("amount"))["total"]), "completed_payments": verified.count()},
            "status_breakdown": [{"status": row["status"], "amount": money(row["total"]), "count": row["count"]} for row in status_totals],
            "monthly": [{"period": row["period"].date().isoformat() if row["period"] else None, "amount": money(row["total"]), "count": row["count"]} for row in monthly],
            "daily": [{"period": row["period"].isoformat() if row["period"] else None, "amount": money(row["total"]), "count": row["count"]} for row in daily],
        })


class EmployerDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in (User.Role.CLIENT, User.Role.ADMIN):
            return Response({"detail": "Only employers or administrators can view employer financials."}, status=status.HTTP_403_FORBIDDEN)
        owner_filter = {} if request.user.role == User.Role.ADMIN else {"task__owner": request.user}
        assignments = Assignment.objects.select_related("task", "worker").filter(**owner_filter)
        transaction_filter = {} if request.user.role == User.Role.ADMIN else {"assignment__task__owner": request.user}
        transactions = Transaction.objects.select_related("assignment__task", "assignment__worker").filter(**transaction_filter)
        verified = transactions.filter(status=Transaction.Status.VERIFIED)
        completed = assignments.filter(task__status=Task.Status.COMPLETED)
        active_tasks = Task.objects.filter(**({} if request.user.role == User.Role.ADMIN else {"owner": request.user})).exclude(status__in=[Task.Status.COMPLETED, Task.Status.CANCELLED]).prefetch_related("applications")
        from apps.applications.models import Application
        applications = Application.objects.filter(**({} if request.user.role == User.Role.ADMIN else {"task__owner": request.user}))
        from apps.complaints.models import Complaint
        reports = Complaint.objects.filter(**({} if request.user.role == User.Role.ADMIN else {"task__owner": request.user}))
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
            "verification": {"status": verification.status, "badge_text": verification.badge_text} if verification else {"status": "ADMIN_SCOPE" if request.user.role == User.Role.ADMIN else "UNVERIFIED", "badge_text": ""},
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
            if transaction.status != Transaction.Status.REFUNDED:
                transaction.status = Transaction.Status.FAILED
                transaction.save(update_fields=["status", "updated_at"])
            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(transaction.assignment.worker, Notification.Kind.PAYMENT_UPDATE, "Payment verified", f"Payment for {transaction.assignment.task.title} was verified.", f"/payments/{transaction.id}")
        return Response(TransactionSerializer(transaction).data)


class PaymentRefundView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "sensitive"

    def post(self, request, pk):
        transaction = get_object_or_404(Transaction.objects.select_related("assignment__task", "assignment__worker"), pk=pk)
        if request.user.role != User.Role.ADMIN and transaction.assignment.task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner or an administrator can refund this payment."}, status=status.HTTP_403_FORBIDDEN)
        was_refunded = transaction.status == Transaction.Status.REFUNDED
        try:
            transaction = refund_test_payment(transaction)
        except PaymentConfigurationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"detail": "The payment provider could not complete the refund. The payment remains verified."}, status=status.HTTP_502_BAD_GATEWAY)
        if not was_refunded:
            from apps.notifications.models import Notification
            from apps.notifications.services import create_notification
            create_notification(transaction.assignment.worker, Notification.Kind.PAYMENT_UPDATE, "Payment refunded", f"Payment for {transaction.assignment.task.title} was refunded.", f"/payments/{transaction.id}")
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
        if transaction.status == Transaction.Status.REFUNDED and event in {"payment.captured", "payment.authorized"}:
            return Response({"received": True, "matched": True, "status": transaction.status})
        if event in {"payment.captured", "payment.authorized"}:
            transaction.status = Transaction.Status.VERIFIED
            transaction.escrow_status = Transaction.EscrowStatus.HELD
            transaction.provider_payment_id = payment_id or transaction.provider_payment_id
        elif event == "payment.failed":
            transaction.status = Transaction.Status.FAILED
        transaction.save(update_fields=["status", "escrow_status", "provider_payment_id", "updated_at"])
        return Response({"received": True, "matched": True, "status": transaction.status})
