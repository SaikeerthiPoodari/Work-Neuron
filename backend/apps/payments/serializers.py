from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source="assignment.task.title", read_only=True)
    task_id = serializers.IntegerField(source="assignment.task_id", read_only=True)
    client_email = serializers.EmailField(source="assignment.task.owner.email", read_only=True)
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "id", "assignment", "assignment_title", "task_id", "client_email", "client_name", "payer", "amount", "currency", "provider",
            "provider_order_id", "provider_payment_id", "status", "created_at", "updated_at",
        )
        read_only_fields = fields

    def get_client_name(self, obj):
        user = obj.assignment.task.owner
        return " ".join(filter(None, [user.first_name, user.last_name])) or user.email


class PaymentVerifySerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()
