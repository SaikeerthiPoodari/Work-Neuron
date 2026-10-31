from django.urls import path

from .views import EmployerDashboardView, PaymentCreateOrderView, PaymentRefundView, PaymentVerifyView, RazorpayWebhookView, TransactionDetailView, TransactionListView


urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("employer-dashboard/", EmployerDashboardView.as_view(), name="employer-dashboard"),
    path("create-order/", PaymentCreateOrderView.as_view(), name="payment-create-order"),
    path("verify/", PaymentVerifyView.as_view(), name="payment-verify"),
    path("<int:pk>/refund/", PaymentRefundView.as_view(), name="payment-refund"),
    path("webhook/", RazorpayWebhookView.as_view(), name="payment-webhook"),
]
