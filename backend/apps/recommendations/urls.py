from django.urls import path

from .views import SmartTaskFeedView, WorkerRecommendationsView


urlpatterns = [
    path("smart-feed/", SmartTaskFeedView.as_view(), name="smart-task-feed"),
    path("workers/", WorkerRecommendationsView.as_view(), name="worker-recommendations"),
]

