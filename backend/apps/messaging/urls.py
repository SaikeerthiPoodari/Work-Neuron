from django.urls import path

from .views import InterviewListCreateView, MessageListCreateView


urlpatterns = [path("messages/", MessageListCreateView.as_view(), name="message-list-create"), path("interviews/", InterviewListCreateView.as_view(), name="interview-list-create")]
