from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Interview, Message
from .serializers import InterviewSerializer, MessageSerializer
from apps.notifications.models import Notification
from apps.notifications.services import create_notification


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Message.objects.filter(Q(sender=user) | Q(recipient=user)).select_related("sender", "recipient")
        if self.request.query_params.get("task"):
            queryset = queryset.filter(task_id=self.request.query_params["task"])
        if self.request.query_params.get("unread") in {"1", "true", "True"}:
            queryset = queryset.filter(recipient=user, read_at__isnull=True)
        return queryset

    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        create_notification(
            message.recipient,
            Notification.Kind.MESSAGE_RECEIVED,
            "New message",
            f"You received a new message about {message.task.title}.",
            f"/messages?task={message.task_id}",
        )


class MessageReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        message = generics.get_object_or_404(Message, pk=pk)
        if message.recipient_id != request.user.id:
            return Response({"detail": "Only the recipient can mark this message as read."}, status=status.HTTP_403_FORBIDDEN)
        if message.read_at is None:
            message.read_at = timezone.now()
            message.save(update_fields=["read_at"])
        return Response(MessageSerializer(message, context={"request": request}).data)


class InterviewListCreateView(generics.ListCreateAPIView):
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Interview.objects.filter(Q(organizer=user) | Q(application__worker=user)).select_related("application", "application__task")

    def perform_create(self, serializer):
        interview = serializer.save(organizer=self.request.user)
        create_notification(
            interview.application.worker,
            Notification.Kind.INTERVIEW_SCHEDULED,
            "Interview scheduled",
            f"An interview for {interview.application.task.title} has been scheduled.",
            "/messages",
        )
