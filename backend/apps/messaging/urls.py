from django.urls import path

from .views import InterviewActionView, InterviewBroadcastView, InterviewListCreateView, MessageListCreateView, MessageReadView


urlpatterns = [path("messages/", MessageListCreateView.as_view(), name="message-list-create"), path("messages/<int:pk>/read/", MessageReadView.as_view(), name="message-read"), path("interviews/broadcast/", InterviewBroadcastView.as_view(), name="interview-broadcast"), path("interviews/<int:pk>/<str:action>/", InterviewActionView.as_view(), name="interview-action"), path("interviews/", InterviewListCreateView.as_view(), name="interview-list-create")]
