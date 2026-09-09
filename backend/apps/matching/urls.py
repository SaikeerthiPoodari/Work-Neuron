from django.urls import path

from .views import TaskWorkerMatchesView


urlpatterns = [path("tasks/<int:pk>/workers/", TaskWorkerMatchesView.as_view(), name="task-worker-matches")]

