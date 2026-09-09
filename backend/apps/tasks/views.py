from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from .models import Task
from .permissions import IsClientRole, IsTaskOwnerOrAdmin
from .serializers import TaskSerializer, TaskTransitionSerializer
from .services import transition_task


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.select_related("owner").prefetch_related("skills")
        user = self.request.user
        if user.role == User.Role.CLIENT:
            queryset = queryset.filter(owner=user)
        elif user.role == User.Role.WORKER:
            queryset = queryset.filter(status__in=[Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED])

        params = self.request.query_params
        search = params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search) | Q(location__icontains=search)
            )
        if params.get("status") and user.role == User.Role.ADMIN:
            queryset = queryset.filter(status=params["status"])
        if params.get("min_budget"):
            queryset = queryset.filter(budget__gte=params["min_budget"])
        if params.get("max_budget"):
            queryset = queryset.filter(budget__lte=params["max_budget"])
        if params.get("location"):
            queryset = queryset.filter(location__icontains=params["location"])
        if params.get("skill"):
            queryset = queryset.filter(skills__id=params["skill"])
        if params.get("deadline_before"):
            queryset = queryset.filter(deadline__lte=params["deadline_before"])
        if params.get("deadline_after"):
            queryset = queryset.filter(deadline__gte=params["deadline_after"])
        return queryset.distinct()

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsClientRole()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.select_related("owner").prefetch_related("skills")

    def check_object_permissions(self, request, obj):
        if request.method in permissions.SAFE_METHODS:
            if request.user.role == User.Role.WORKER and obj.status not in (Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED):
                self.permission_denied(request, message="This task is not available to workers.")
            return
        if not (request.user.role == User.Role.ADMIN or obj.owner_id == request.user.id):
            self.permission_denied(request, message="Only the task owner or an administrator can modify this task.")

    def perform_update(self, serializer):
        serializer.save()


class TaskTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrAdmin]

    def post(self, request, pk):
        task = generics.get_object_or_404(Task, pk=pk)
        self.check_object_permissions(request, task)
        serializer = TaskTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            task = transition_task(task, serializer.validated_data["status"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TaskSerializer(task, context={"request": request}).data)

