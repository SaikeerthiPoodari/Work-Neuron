from django.urls import path

from .views import DailyWageJobsView, EventJobsView, FestivalJobsView, PartTimeJobsView, TaskDecompositionView, TaskDetailView, TaskListCreateView, TaskTransitionView, WeekendJobsView


urlpatterns = [
    path("", TaskListCreateView.as_view(), name="task-list-create"),
    path("daily-wage/", DailyWageJobsView.as_view(), name="daily-wage-jobs"),
    path("part-time/", PartTimeJobsView.as_view(), name="part-time-jobs"),
    path("weekend/", WeekendJobsView.as_view(), name="weekend-jobs"),
    path("event/", EventJobsView.as_view(), name="event-jobs"),
    path("festival/", FestivalJobsView.as_view(), name="festival-jobs"),
    path("<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("<int:pk>/transition/", TaskTransitionView.as_view(), name="task-transition"),
    path("<int:pk>/decomposition/", TaskDecompositionView.as_view(), name="task-decomposition"),
]
