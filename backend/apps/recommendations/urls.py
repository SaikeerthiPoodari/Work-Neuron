from django.urls import path

from .views import JobRecommendationsView, SmartTaskFeedView, WorkerRecommendationsView, WorkerSkillGapView


urlpatterns = [
    path("smart-feed/", SmartTaskFeedView.as_view(), name="smart-task-feed"),
    path("jobs/", JobRecommendationsView.as_view(), name="job-recommendations"),
    path("workers/", WorkerRecommendationsView.as_view(), name="worker-recommendations"),
    path("skill-gap/", WorkerSkillGapView.as_view(), name="worker-skill-gap"),
]
