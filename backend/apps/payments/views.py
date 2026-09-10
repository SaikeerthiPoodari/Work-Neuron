from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.assignments.models import Assignment

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


class PaymentCreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

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
