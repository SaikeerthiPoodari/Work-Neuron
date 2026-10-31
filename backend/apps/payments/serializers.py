from rest_framework import serializers

from .models import BankAccount, PaymentMethod, PaymentProfile, PayoutRecord, Transaction


class TransactionSerializer(serializers.ModelSerializer):
    assignment_title = serializers.CharField(source="assignment.task.title", read_only=True)
    task_id = serializers.IntegerField(source="assignment.task_id", read_only=True)
    client_email = serializers.EmailField(source="assignment.task.owner.email", read_only=True)
    client_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "id", "assignment", "assignment_title", "task_id", "client_email", "client_name", "payer", "amount", "currency", "provider",
            "provider_order_id", "provider_payment_id", "status", "escrow_status", "created_at", "updated_at",
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


class BankAccountSerializer(serializers.ModelSerializer):
    masked_account_number = serializers.SerializerMethodField()
    confirm_account_number = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = BankAccount
        fields = ("id", "holder_name", "bank_name", "account_number", "confirm_account_number", "masked_account_number", "ifsc_code", "account_type", "upi_id", "is_primary", "verification_status", "created_at", "updated_at")
        extra_kwargs = {"account_number": {"write_only": True}}
        read_only_fields = ("id", "masked_account_number", "verification_status", "created_at", "updated_at")

    def validate(self, attrs):
        confirm = attrs.pop("confirm_account_number", None)
        if self.instance and attrs.get("account_number", None) == "" and confirm == "":
            attrs.pop("account_number", None)
            return attrs
        if confirm is not None and confirm != attrs.get("account_number"):
            raise serializers.ValidationError({"confirm_account_number": "Account numbers do not match."})
        if not self.instance and not confirm:
            raise serializers.ValidationError({"confirm_account_number": "Confirm the account number."})
        return attrs

    def get_masked_account_number(self, obj):
        value = obj.account_number or ""
        return f"{'*' * max(0, len(value) - 4)}{value[-4:]}" if value else ""


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ("id", "method_type", "display_label", "verification_status", "is_primary", "created_at", "updated_at")
        read_only_fields = ("id", "verification_status", "created_at", "updated_at")


class PaymentProfileSerializer(serializers.ModelSerializer):
    workneuron_id = serializers.CharField(source="user_id", read_only=True)
    name = serializers.SerializerMethodField()
    qr_payload = serializers.SerializerMethodField()
    pin_set = serializers.SerializerMethodField()

    class Meta:
        model = PaymentProfile
        fields = ("workneuron_id", "name", "qr_token", "qr_revoked", "qr_payload", "pin_set", "created_at", "updated_at")
        read_only_fields = fields

    def get_name(self, obj):
        return " ".join(filter(None, [obj.user.first_name, obj.user.last_name])) or obj.user.email

    def get_qr_payload(self, obj):
        request = self.context.get("request")
        path = f"/payments/qr/{obj.qr_token}/"
        return request.build_absolute_uri(path) if request else path

    def get_pin_set(self, obj):
        return bool(obj.pin_hash)


class PayoutRecordSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source="transaction.assignment.task.title", read_only=True)

    class Meta:
        model = PayoutRecord
        fields = ("id", "transaction", "task_title", "amount", "status", "provider_reference", "created_at", "updated_at")
