from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tasks.models import Task
from apps.tasks.services import transition_task

from .models import Assignment
from .permissions import IsWorkerRole
from .serializers import AssignmentSerializer, CompletionSerializer, ProgressSerializer, SubmissionSerializer


class AssignmentListView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Assignment.objects.select_related("task", "worker", "application")
        user = self.request.user
        if user.role == User.Role.WORKER:
            return queryset.filter(worker=user)
        if user.role == User.Role.CLIENT:
            return queryset.filter(task__owner=user)
        return queryset


class AssignmentDetailView(generics.RetrieveAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Assignment.objects.select_related("task", "worker", "application")
        user = self.request.user
        if user.role == User.Role.WORKER:
            return queryset.filter(worker=user)
        if user.role == User.Role.CLIENT:
            return queryset.filter(task__owner=user)
        return queryset


class AssignmentStartView(APIView):
    permission_classes = [IsWorkerRole]

    @transaction.atomic
    def post(self, request, pk):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task"), pk=pk)
        if assignment.worker_id != request.user.id:
            return Response({"detail": "Only the assigned worker can start this task."}, status=status.HTTP_403_FORBIDDEN)
        if assignment.task.status != Task.Status.ASSIGNED:
            return Response({"detail": "Only assigned tasks can be started."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            transition_task(assignment.task, Task.Status.IN_PROGRESS)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        assignment.started_at = timezone.now()
        assignment.save(update_fields=["started_at", "updated_at"])
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(assignment.task.owner, Notification.Kind.TASK_STATUS_CHANGED, "Task started", f"{request.user.email} started {assignment.task.title}.", f"/assignments/{assignment.id}")
        return Response(AssignmentSerializer(assignment).data)


class AssignmentProgressView(APIView):
    permission_classes = [IsWorkerRole]

    def patch(self, request, pk):
        assignment = generics.get_object_or_404(Assignment.objects.select_related("task"), pk=pk)
        if assignment.worker_id != request.user.id:
            return Response({"detail": "Only the assigned worker can update progress."}, status=status.HTTP_403_FORBIDDEN)
        if assignment.task.status != Task.Status.IN_PROGRESS:
            return Response({"detail": "Progress can be updated only while a task is in progress."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment.progress = serializer.validated_data["progress"]
        assignment.save(update_fields=["progress", "updated_at"])
        return Response(AssignmentSerializer(assignment).data)


class AssignmentSubmitView(APIView):
    permission_classes = [IsWorkerRole]

    @transaction.atomic
    def post(self, request, pk):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task"), pk=pk)
        if assignment.worker_id != request.user.id:
            return Response({"detail": "Only the assigned worker can submit this task."}, status=status.HTTP_403_FORBIDDEN)
        if assignment.task.status != Task.Status.IN_PROGRESS:
            return Response({"detail": "Only in-progress tasks can be submitted."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = SubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            transition_task(assignment.task, Task.Status.SUBMITTED)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        assignment.submission = serializer.validated_data["submission"]
        assignment.progress = 100
        assignment.submitted_at = timezone.now()
        assignment.save(update_fields=["submission", "progress", "submitted_at", "updated_at"])
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(assignment.task.owner, Notification.Kind.TASK_SUBMITTED, "Task submitted", f"Work was submitted for {assignment.task.title}.", f"/assignments/{assignment.id}")
        return Response(AssignmentSerializer(assignment).data)


class AssignmentCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task"), pk=pk)
        if request.user.role != User.Role.ADMIN and assignment.task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner or an administrator can complete this task."}, status=status.HTTP_403_FORBIDDEN)
        if assignment.task.status != Task.Status.SUBMITTED:
            return Response({"detail": "Only submitted tasks can be completed."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            transition_task(assignment.task, Task.Status.COMPLETED)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        assignment.client_feedback = serializer.validated_data.get("client_feedback", "")
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=["client_feedback", "completed_at", "updated_at"])
        from apps.search.services import record_task_event
        record_task_event(assignment.worker, assignment.task, "COMPLETE")
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(assignment.worker, Notification.Kind.TASK_COMPLETED, "Task completed", f"{assignment.task.title} was marked completed.", f"/assignments/{assignment.id}")
        return Response(AssignmentSerializer(assignment).data)
