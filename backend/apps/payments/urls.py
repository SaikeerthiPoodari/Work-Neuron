from django.urls import path

from .views import EmployerDashboardView, PaymentCreateOrderView, PaymentVerifyView, RazorpayWebhookView, TransactionListView


urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("employer-dashboard/", EmployerDashboardView.as_view(), name="employer-dashboard"),
    path("create-order/", PaymentCreateOrderView.as_view(), name="payment-create-order"),
    path("verify/", PaymentVerifyView.as_view(), name="payment-verify"),
    path("webhook/", RazorpayWebhookView.as_view(), name="payment-webhook"),
]
