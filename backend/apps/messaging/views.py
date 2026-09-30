from django.db.models import Q
from rest_framework import generics, permissions

from .models import Interview, Message
from .serializers import InterviewSerializer, MessageSerializer


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Message.objects.filter(Q(sender=user) | Q(recipient=user)).select_related("sender", "recipient")
        if self.request.query_params.get("task"):
            queryset = queryset.filter(task_id=self.request.query_params["task"])
        return queryset

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class InterviewListCreateView(generics.ListCreateAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Interview.objects.filter(Q(organizer=user) | Q(application__worker=user)).select_related("application", "application__task")

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)
