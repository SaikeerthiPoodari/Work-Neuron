from django.urls import path

from .views import FraudAlertDetailView, FraudAlertListView, FraudScanView


urlpatterns = [
    path("alerts/", FraudAlertListView.as_view(), name="fraud-alert-list"),
    path("scan/", FraudScanView.as_view(), name="fraud-scan"),
    path("alerts/<int:pk>/", FraudAlertDetailView.as_view(), name="fraud-alert-detail"),
]

