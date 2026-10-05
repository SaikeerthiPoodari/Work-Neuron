from django.urls import path

from .views import EmployerVerificationView, VerificationDocumentCreateView, WorkerDirectoryView

urlpatterns = [
    path("verification/", EmployerVerificationView.as_view(), name="employer-verification"),
    path("verification/documents/", VerificationDocumentCreateView.as_view(), name="employer-verification-document"),
    path("workers/", WorkerDirectoryView.as_view(), name="worker-directory"),
]
