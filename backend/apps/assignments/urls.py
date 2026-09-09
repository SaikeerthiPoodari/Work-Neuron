from django.urls import path

from .views import (
    AssignmentCompleteView,
    AssignmentDetailView,
    AssignmentListView,
    AssignmentProgressView,
    AssignmentStartView,
    AssignmentSubmitView,
)


urlpatterns = [
    path("", AssignmentListView.as_view(), name="assignment-list"),
    path("<int:pk>/", AssignmentDetailView.as_view(), name="assignment-detail"),
    path("<int:pk>/start/", AssignmentStartView.as_view(), name="assignment-start"),
    path("<int:pk>/progress/", AssignmentProgressView.as_view(), name="assignment-progress"),
    path("<int:pk>/submit/", AssignmentSubmitView.as_view(), name="assignment-submit"),
    path("<int:pk>/complete/", AssignmentCompleteView.as_view(), name="assignment-complete"),
]

