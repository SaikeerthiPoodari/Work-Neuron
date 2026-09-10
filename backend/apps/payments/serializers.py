from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source="assignment.task.title", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id", "assignment", "assignment_title", "payer", "amount", "currency", "provider",
            "provider_order_id", "provider_payment_id", "status", "created_at", "updated_at",
        )
        read_only_fields = fields


class PaymentVerifySerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()

