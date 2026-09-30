from django.urls import path

from .views import AdminVerificationActionView, AdminVerificationDocumentView, AdminVerificationListView

urlpatterns = [
    path("verifications/", AdminVerificationListView.as_view(), name="admin-verification-list"),
    path("verifications/<int:pk>/action/", AdminVerificationActionView.as_view(), name="admin-verification-action"),
    path("verification-documents/<int:pk>/", AdminVerificationDocumentView.as_view(), name="admin-verification-document"),
]
