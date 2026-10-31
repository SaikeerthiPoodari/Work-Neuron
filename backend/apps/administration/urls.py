from django.urls import path

from .views import (
    AdminApplicationListView,
    AdminAssignmentListView,
    AdminComplaintListView,
    AdminFraudAlertListView,
    AdminTaskListView,
    AdminTransactionListView,
    AdminUserDetailView,
    AdminUserListView,
    AdminAuditEventListView,
)


urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("users/<int:pk>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("audit-events/", AdminAuditEventListView.as_view(), name="admin-audit-event-list"),
    path("tasks/", AdminTaskListView.as_view(), name="admin-task-list"),
    path("applications/", AdminApplicationListView.as_view(), name="admin-application-list"),
    path("assignments/", AdminAssignmentListView.as_view(), name="admin-assignment-list"),
    path("transactions/", AdminTransactionListView.as_view(), name="admin-transaction-list"),
    path("complaints/", AdminComplaintListView.as_view(), name="admin-complaint-list"),
    path("fraud-alerts/", AdminFraudAlertListView.as_view(), name="admin-fraud-alert-list"),
]

