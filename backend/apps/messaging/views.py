from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Interview, Message
from .serializers import InterviewSerializer, MessageSerializer
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.applications.models import Application
from apps.tasks.models import Task


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


class InterviewBroadcastView(APIView):
    """Explicit all-applicant scheduling; creates one auditable interview per applicant."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != "CLIENT":
            return Response({"detail": "Only clients can broadcast interview invitations."}, status=status.HTTP_403_FORBIDDEN)
        task = generics.get_object_or_404(Task, pk=request.data.get("task"), owner=request.user)
        eligible = Application.objects.filter(task=task, status__in=[Application.Status.SUBMITTED, Application.Status.ACCEPTED]).select_related("worker")
        created = []
        for application in eligible:
            payload = {**request.data, "application": application.id}
            serializer = InterviewSerializer(data=payload, context={"request": request})
            serializer.is_valid(raise_exception=True)
            interview = serializer.save(organizer=request.user)
            created.append(interview)
            create_notification(interview.application.worker, Notification.Kind.INTERVIEW_SCHEDULED, "Interview announcement", f"An interview announcement for {task.title} has been scheduled.", "/messages")
        return Response(InterviewSerializer(created, many=True).data, status=status.HTTP_201_CREATED)


class InterviewActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, action):
        interview = generics.get_object_or_404(Interview.objects.select_related("application__worker", "application__task"), pk=pk)
        if interview.organizer_id != request.user.id:
            return Response({"detail": "Only the interview organizer can change interview details."}, status=status.HTTP_403_FORBIDDEN)
        if action == "cancel":
            interview.status = Interview.Status.CANCELLED
            interview.save(update_fields=["status"])
            create_notification(interview.application.worker, Notification.Kind.INTERVIEW_SCHEDULED, "Interview cancelled", f"The interview for {interview.application.task.title} was cancelled.", "/messages")
        elif action == "reschedule":
            serializer = InterviewSerializer(interview, data=request.data, partial=True, context={"request": request})
            serializer.is_valid(raise_exception=True)
            interview = serializer.save(status=Interview.Status.SCHEDULED)
            create_notification(interview.application.worker, Notification.Kind.INTERVIEW_SCHEDULED, "Interview rescheduled", f"The interview for {interview.application.task.title} has new details.", "/messages")
        else:
            return Response({"detail": "Unsupported interview action."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(InterviewSerializer(interview).data)
