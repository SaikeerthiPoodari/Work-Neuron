from django.urls import path

from .views import (
    AssignmentCompleteView,
    AssignmentDetailView,
    AssignmentLevelReviewView,
    AssignmentLevelSubmitView,
    AssignmentLevelTaskCompleteView,
    ClientAssignmentLevelTaskCompleteView,
    AssignmentLevelsConfigView,
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
    path("<int:pk>/levels/", AssignmentLevelsConfigView.as_view(), name="assignment-levels-config"),
    path("<int:pk>/levels/<int:level_id>/submit/", AssignmentLevelSubmitView.as_view(), name="assignment-level-submit"),
    path("<int:pk>/levels/<int:level_id>/tasks/<int:task_id>/complete/", AssignmentLevelTaskCompleteView.as_view(), name="assignment-level-task-complete"),
    path("<int:pk>/levels/<int:level_id>/tasks/<int:task_id>/client-complete/", ClientAssignmentLevelTaskCompleteView.as_view(), name="assignment-level-client-task-complete"),
    path("<int:pk>/levels/<int:level_id>/review/", AssignmentLevelReviewView.as_view(), name="assignment-level-review"),
]
