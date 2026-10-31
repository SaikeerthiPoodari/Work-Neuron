from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tasks.models import Task
from apps.tasks.services import transition_task
from apps.payments.services import release_escrow_for_assignment

from .models import Assignment, AssignmentLevel, AssignmentLevelTask
from .permissions import IsWorkerRole
from .serializers import (AssignmentSerializer, AssignmentLevelsConfigSerializer, CompletionSerializer,
                          LevelReviewSerializer, LevelSubmissionSerializer, ProgressSerializer, SubmissionSerializer)


class AssignmentListView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Assignment.objects.select_related("task", "worker", "worker__worker_profile", "application").prefetch_related("levels", "transactions")
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
        queryset = Assignment.objects.select_related("task", "worker", "worker__worker_profile", "application").prefetch_related("levels", "transactions")
        user = self.request.user
        if user.role == User.Role.WORKER:
            return queryset.filter(worker=user)
        if user.role == User.Role.CLIENT:
            return queryset.filter(task__owner=user)
        return queryset


class AssignmentStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task"), pk=pk)
        is_worker = assignment.worker_id == request.user.id
        is_client = assignment.task.owner_id == request.user.id
        if request.user.role != User.Role.ADMIN and not (is_worker or is_client):
            return Response({"detail": "Only the assigned client or worker can confirm the start."}, status=status.HTTP_403_FORBIDDEN)
        if assignment.task.status != Task.Status.ASSIGNED:
            return Response({"detail": "Start confirmation is only available for assigned tasks."}, status=status.HTTP_400_BAD_REQUEST)
        if not assignment.levels.exists():
            return Response({"detail": "The client must configure assignment levels before work can start."}, status=status.HTTP_400_BAD_REQUEST)
        funded = assignment.transactions.filter(status="VERIFIED", escrow_status="HELD").exists()
        if not funded:
            return Response({"detail": "The client must successfully fund the task before either party can start it."}, status=status.HTTP_400_BAD_REQUEST)
        now = timezone.now()
        if is_worker or request.user.role == User.Role.ADMIN:
            assignment.worker_started_at = assignment.worker_started_at or now
        if is_client or request.user.role == User.Role.ADMIN:
            assignment.client_started_at = assignment.client_started_at or now
        fields = ["worker_started_at", "client_started_at", "updated_at"]
        if assignment.worker_started_at and assignment.client_started_at:
            transition_task(assignment.task, Task.Status.IN_PROGRESS)
            assignment.started_at = assignment.started_at or now
            fields += ["started_at"]
        assignment.save(update_fields=fields)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        other = assignment.worker if is_client else assignment.task.owner
        create_notification(other, Notification.Kind.TASK_STATUS_CHANGED, "Start confirmation received", f"{request.user.email} confirmed the start of {assignment.task.title}." if assignment.task.status == Task.Status.ASSIGNED else f"{assignment.task.title} is now in progress.", f"/assignments/{assignment.id}")
        return Response(AssignmentSerializer(assignment).data)


class AssignmentProgressView(APIView):
    permission_classes = [IsWorkerRole]

    def patch(self, request, pk):
        return Response({"detail": "Progress is calculated from completed assignment levels."}, status=status.HTTP_410_GONE)


class AssignmentSubmitView(APIView):
    permission_classes = [IsWorkerRole]

    @transaction.atomic
    def post(self, request, pk):
        return Response({"detail": "Submit work for the current level using its level submission action."}, status=status.HTTP_410_GONE)


class AssignmentLevelsConfigView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def put(self, request, pk):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task").prefetch_related("levels"), pk=pk)
        if request.user.role != User.Role.ADMIN and assignment.task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner can configure assignment levels."}, status=status.HTTP_403_FORBIDDEN)
        if assignment.started_at or assignment.task.status != Task.Status.ASSIGNED:
            return Response({"detail": "Levels can only be configured before work starts."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AssignmentLevelsConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        levels_data = serializer.validated_data["levels"]
        if all(values.get("payment_amount") is None for values in levels_data):
            levels_data[0]["payment_amount"] = assignment.task.budget
            for values in levels_data[1:]:
                values["payment_amount"] = Decimal("0")
        total = sum((Decimal(values.get("payment_amount", 0)) for values in levels_data), Decimal("0"))
        if total != assignment.task.budget:
            return Response({"detail": f"Milestone allocations must total exactly {assignment.task.budget} {getattr(assignment.task, 'currency', 'INR')}."}, status=status.HTTP_400_BAD_REQUEST)
        assignment.levels.all().delete()
        for index, values in enumerate(levels_data, start=1):
            tasks = list(dict.fromkeys(task.strip() for task in values.pop("tasks", []) if task.strip()))
            level = AssignmentLevel.objects.create(assignment=assignment, order=index, status=AssignmentLevel.Status.CURRENT if index == 1 else AssignmentLevel.Status.LOCKED, **values)
            AssignmentLevelTask.objects.bulk_create([AssignmentLevelTask(level=level, title=title) for title in tasks])
        assignment.progress = 0
        assignment.save(update_fields=["progress", "updated_at"])
        assignment._prefetched_objects_cache.pop("levels", None)
        return Response(AssignmentSerializer(assignment).data)


class AssignmentLevelSubmitView(APIView):
    permission_classes = [IsWorkerRole]

    @transaction.atomic
    def post(self, request, pk, level_id):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task", "worker").prefetch_related("levels"), pk=pk)
        if assignment.worker_id != request.user.id:
            return Response({"detail": "Only the assigned worker can submit work."}, status=status.HTTP_403_FORBIDDEN)
        level = generics.get_object_or_404(AssignmentLevel.objects.select_for_update(), pk=level_id, assignment=assignment)
        if level.status != AssignmentLevel.Status.CURRENT or assignment.task.status not in (Task.Status.IN_PROGRESS, Task.Status.SUBMITTED):
            return Response({"detail": "Only the current level can be submitted while the assignment is in progress."}, status=status.HTTP_400_BAD_REQUEST)
        if level.checklist_items.filter(is_completed=False).exists():
            return Response({"detail": "Complete all required checklist tasks before submitting this level."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LevelSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not assignment.levels.filter(order__gt=level.order).exists() and assignment.task.status == Task.Status.IN_PROGRESS:
            try:
                transition_task(assignment.task, Task.Status.SUBMITTED)
            except DjangoValidationError as exc:
                return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        level.submission = serializer.validated_data["submission"]
        level.status = AssignmentLevel.Status.SUBMITTED
        level.submitted_at = timezone.now()
        level.save(update_fields=["submission", "status", "submitted_at"])
        assignment.submission = level.submission
        assignment.submitted_at = level.submitted_at
        assignment.save(update_fields=["submission", "submitted_at", "updated_at"])
        assignment._prefetched_objects_cache.pop("levels", None)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(assignment.task.owner, Notification.Kind.TASK_SUBMITTED, "Assignment level submitted", f"Level {level.order} was submitted for {assignment.task.title}.", f"/assignments/{assignment.id}")
        return Response(AssignmentSerializer(assignment).data)


class AssignmentLevelTaskCompleteView(APIView):
    permission_classes = [IsWorkerRole]

    @transaction.atomic
    def post(self, request, pk, level_id, task_id):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task").prefetch_related("levels__checklist_items"), pk=pk)
        if assignment.worker_id != request.user.id:
            return Response({"detail": "Only the assigned worker can complete checklist tasks."}, status=status.HTTP_403_FORBIDDEN)
        level = generics.get_object_or_404(AssignmentLevel.objects.select_for_update(), pk=level_id, assignment=assignment)
        if level.status != AssignmentLevel.Status.CURRENT:
            return Response({"detail": "Only checklist tasks in the current level can be completed."}, status=status.HTTP_400_BAD_REQUEST)
        item = generics.get_object_or_404(AssignmentLevelTask.objects.select_for_update(), pk=task_id, level=level)
        if not item.is_completed:
            item.is_completed = True
            item.completed_at = timezone.now()
            item.completed_by = request.user
            item.save(update_fields=["is_completed", "completed_at", "completed_by"])
        assignment._prefetched_objects_cache.pop("levels", None)
        return Response(AssignmentSerializer(assignment).data)


class ClientAssignmentLevelTaskCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, level_id, task_id):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task").prefetch_related("levels__checklist_items"), pk=pk)
        if request.user.role != User.Role.ADMIN and assignment.task.owner_id != request.user.id:
            return Response({"detail": "Only the client can confirm this checklist task."}, status=status.HTTP_403_FORBIDDEN)
        level = generics.get_object_or_404(AssignmentLevel.objects.select_for_update(), pk=level_id, assignment=assignment)
        if level.status not in (AssignmentLevel.Status.CURRENT, AssignmentLevel.Status.SUBMITTED):
            return Response({"detail": "Only the active level can be confirmed."}, status=status.HTTP_400_BAD_REQUEST)
        item = generics.get_object_or_404(AssignmentLevelTask.objects.select_for_update(), pk=task_id, level=level)
        if not item.client_completed:
            item.client_completed = True
            item.client_completed_at = timezone.now()
            item.client_completed_by = request.user
            item.save(update_fields=["client_completed", "client_completed_at", "client_completed_by"])
        assignment._prefetched_objects_cache.pop("levels", None)
        return Response(AssignmentSerializer(assignment).data)


class AssignmentLevelReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk, level_id):
        assignment = generics.get_object_or_404(Assignment.objects.select_for_update().select_related("task").prefetch_related("levels"), pk=pk)
        if request.user.role != User.Role.ADMIN and assignment.task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner can review submissions."}, status=status.HTTP_403_FORBIDDEN)
        level = generics.get_object_or_404(AssignmentLevel.objects.select_for_update(), pk=level_id, assignment=assignment)
        if level.status != AssignmentLevel.Status.SUBMITTED:
            return Response({"detail": "This level has no submission awaiting review."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LevelReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["action"] == "approve" and level.checklist_items.filter(client_completed=False).exists():
            return Response({"detail": "Confirm every checklist item as the client before approving this level."}, status=status.HTTP_400_BAD_REQUEST)
        level.feedback = serializer.validated_data.get("feedback", "")
        level.reviewed_at = timezone.now()
        if serializer.validated_data["action"] == "changes":
            level.status = AssignmentLevel.Status.CURRENT
        else:
            level.status = AssignmentLevel.Status.COMPLETED
            next_level = assignment.levels.filter(order__gt=level.order).order_by("order").first()
            if next_level:
                next_level.status = AssignmentLevel.Status.CURRENT
                next_level.save(update_fields=["status"])
            else:
                try:
                    if assignment.task.status == Task.Status.IN_PROGRESS:
                        transition_task(assignment.task, Task.Status.SUBMITTED)
                    transition_task(assignment.task, Task.Status.COMPLETED)
                except DjangoValidationError as exc:
                    return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
                assignment.completed_at = timezone.now()
                assignment.client_feedback = level.feedback
        level.save(update_fields=["status", "feedback", "reviewed_at"])
        total = assignment.levels.count()
        done = assignment.levels.filter(status=AssignmentLevel.Status.COMPLETED).count()
        assignment.progress = round(done * 100 / total) if total else 0
        if done == total:
            assignment.completed_at = assignment.completed_at or timezone.now()
        assignment.save(update_fields=["progress", "completed_at", "updated_at"])
        assignment._prefetched_objects_cache.pop("levels", None)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        if done == total:
            release_escrow_for_assignment(assignment)
            from apps.search.services import record_task_event
            record_task_event(assignment.worker, assignment.task, "COMPLETE")
            from apps.profiles.services import refresh_professional_portfolio
            refresh_professional_portfolio(assignment.worker)
            create_notification(assignment.worker, Notification.Kind.TASK_COMPLETED, "Task completed", f"{assignment.task.title} was marked completed.", f"/assignments/{assignment.id}")
        elif serializer.validated_data["action"] == "approve":
            create_notification(assignment.worker, Notification.Kind.TASK_STATUS_CHANGED, "Next level unlocked", f"Level {level.order + 1} is ready for {assignment.task.title}.", f"/assignments/{assignment.id}")
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
        if assignment.levels.exists():
            return Response({"detail": "Assignments with levels are completed by approving the final level."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CompletionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            transition_task(assignment.task, Task.Status.COMPLETED)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        assignment.client_feedback = serializer.validated_data.get("client_feedback", "")
        assignment.completed_at = timezone.now()
        assignment.save(update_fields=["client_feedback", "completed_at", "updated_at"])
        release_escrow_for_assignment(assignment)
        from apps.search.services import record_task_event
        record_task_event(assignment.worker, assignment.task, "COMPLETE")
        from apps.profiles.services import refresh_professional_portfolio
        refresh_professional_portfolio(assignment.worker)
        from apps.notifications.models import Notification
        from apps.notifications.services import create_notification
        create_notification(assignment.worker, Notification.Kind.TASK_COMPLETED, "Task completed", f"{assignment.task.title} was marked completed.", f"/assignments/{assignment.id}")
        return Response(AssignmentSerializer(assignment).data)
