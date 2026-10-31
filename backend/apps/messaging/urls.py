from django.urls import path

from .views import InterviewListCreateView, MessageListCreateView, MessageReadView


urlpatterns = [path("messages/", MessageListCreateView.as_view(), name="message-list-create"), path("messages/<int:pk>/read/", MessageReadView.as_view(), name="message-read"), path("interviews/", InterviewListCreateView.as_view(), name="interview-list-create")]
