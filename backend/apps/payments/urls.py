from django.urls import path

from .views import BankAccountDetailView, BankAccountListCreateView, EmployerDashboardView, PaymentAnalyticsView, PaymentCreateOrderView, PaymentMethodListCreateView, PaymentPinView, PaymentQrResolveView, PaymentQrView, PaymentRefundView, PaymentVerifyView, RazorpayWebhookView, TransactionDetailView, TransactionListView, WalletOverviewView


urlpatterns = [
    path("wallet/", WalletOverviewView.as_view(), name="wallet-overview"),
    path("bank-accounts/", BankAccountListCreateView.as_view(), name="bank-account-list"),
    path("bank-accounts/<int:pk>/", BankAccountDetailView.as_view(), name="bank-account-detail"),
    path("payment-methods/", PaymentMethodListCreateView.as_view(), name="payment-method-list"),
    path("pin/", PaymentPinView.as_view(), name="payment-pin"),
    path("qr/", PaymentQrView.as_view(), name="payment-qr"),
    path("qr/<str:token>/", PaymentQrResolveView.as_view(), name="payment-qr-resolve"),
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("employer-dashboard/", EmployerDashboardView.as_view(), name="employer-dashboard"),
    path("analytics/", PaymentAnalyticsView.as_view(), name="payment-analytics"),
    path("create-order/", PaymentCreateOrderView.as_view(), name="payment-create-order"),
    path("verify/", PaymentVerifyView.as_view(), name="payment-verify"),
    path("<int:pk>/refund/", PaymentRefundView.as_view(), name="payment-refund"),
    path("webhook/", RazorpayWebhookView.as_view(), name="payment-webhook"),
]
