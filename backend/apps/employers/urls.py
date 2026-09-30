from django.urls import path

from .views import EmployerVerificationView, VerificationDocumentCreateView

urlpatterns = [
    path("verification/", EmployerVerificationView.as_view(), name="employer-verification"),
    path("verification/documents/", VerificationDocumentCreateView.as_view(), name="employer-verification-document"),
]
