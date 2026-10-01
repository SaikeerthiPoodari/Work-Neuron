from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from math import asin, cos, radians, sin, sqrt
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from ai_engine.recommendations.decomposition import decompose_task

from .models import Task
from .permissions import IsClientRole, IsTaskOwnerOrAdmin
from .serializers import TaskSerializer, TaskTransitionSerializer
from .services import transition_task


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.select_related("owner", "owner__client_profile").prefetch_related("skills")
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
                | Q(location_city__icontains=search) | Q(location_area__icontains=search)
                | Q(location_state__icontains=search) | Q(category__icontains=search)
            )
        if params.get("status") and user.role == User.Role.ADMIN:
            queryset = queryset.filter(status=params["status"])
        if params.get("min_budget"):
            queryset = queryset.filter(budget__gte=params["min_budget"])
        if params.get("max_budget"):
            queryset = queryset.filter(budget__lte=params["max_budget"])
        if params.get("location"):
            location = params["location"]
            queryset = queryset.filter(Q(location__icontains=location) | Q(location_city__icontains=location) | Q(location_area__icontains=location) | Q(location_state__icontains=location))
        if params.get("skill"):
            queryset = queryset.filter(skills__id=params["skill"])
        job_type = params.get("job_type") or getattr(self, "forced_job_type", "")
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        if params.get("category"):
            queryset = queryset.filter(category__icontains=params["category"])
        if params.get("education"):
            queryset = queryset.filter(education_requirement__icontains=params["education"])
        if params.get("experience"):
            queryset = queryset.filter(experience_requirement__icontains=params["experience"])
        if params.get("working_hours"):
            queryset = queryset.filter(working_hours__icontains=params["working_hours"])
        if params.get("employer_type"):
            queryset = queryset.filter(owner__employer_verification__employer_type=params["employer_type"])
        if params.get("verified") in {"1", "true", "True"}:
            queryset = queryset.filter(owner__employer_verification__status="VERIFIED")
        if params.get("salary_type"):
            queryset = queryset.filter(salary_type=params["salary_type"])
        for field in ("location_city", "location_area", "location_state"):
            if params.get(field):
                queryset = queryset.filter(**{f"{field}__icontains": params[field]})
        if params.get("work_mode"):
            queryset = queryset.filter(work_mode=params["work_mode"])
        if params.get("deadline_before"):
            queryset = queryset.filter(deadline__lte=params["deadline_before"])
        if params.get("deadline_after"):
            queryset = queryset.filter(deadline__gte=params["deadline_after"])
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        latitude, longitude = request.query_params.get("latitude"), request.query_params.get("longitude")
        if latitude and longitude:
            try:
                origin_lat, origin_lon = float(latitude), float(longitude)
                radius = float(request.query_params.get("radius_km", 50))
                if not (-90 <= origin_lat <= 90 and -180 <= origin_lon <= 180) or radius <= 0:
                    raise ValueError
                nearby = []
                for task in queryset:
                    if task.is_remote or (task.work_mode == Task.WorkMode.REMOTE and task.latitude is None and task.longitude is None):
                        task.distance_km = None
                        nearby.append(task)
                        continue
                    if task.latitude is None or task.longitude is None:
                        continue
                    task_lat, task_lon = float(task.latitude), float(task.longitude)
                    # Legacy rows may predate coordinate validators. Ignore invalid map
                    # locations safely instead of letting malformed data break the feed.
                    if not (-90 <= task_lat <= 90 and -180 <= task_lon <= 180):
                        continue
                    d_lat, d_lon = radians(task_lat - origin_lat), radians(task_lon - origin_lon)
                    value = sin(d_lat / 2) ** 2 + cos(radians(origin_lat)) * cos(radians(task_lat)) * sin(d_lon / 2) ** 2
                    distance = 6371 * 2 * asin(sqrt(value))
                    if distance <= radius:
                        task.distance_km = round(distance, 2)
                        nearby.append(task)
                sort = request.query_params.get("sort", "distance")
                if sort == "salary":
                    queryset = sorted(nearby, key=lambda task: task.budget, reverse=True)
                elif sort == "newest":
                    queryset = sorted(nearby, key=lambda task: task.created_at, reverse=True)
                else:
                    queryset = sorted(nearby, key=lambda task: task.distance_km is None if nearby else False)
                    queryset = sorted(queryset, key=lambda task: task.distance_km if task.distance_km is not None else float("inf"))
            except (TypeError, ValueError):
                return Response({"detail": "latitude, longitude, and radius_km must be valid numbers."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(queryset, many=True)
        if latitude and longitude:
            data = [dict(item, distance_km=task.distance_km) for item, task in zip(serializer.data, queryset)]
            return Response(data)
        data = serializer.data
        sort = request.query_params.get("sort")
        if sort == "salary":
            data = sorted(data, key=lambda item: float(item.get("budget", 0)), reverse=True)
        elif sort == "newest":
            data = sorted(data, key=lambda item: item.get("created_at", ""), reverse=True)
        return Response(data)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsClientRole()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class JobSectionView(TaskListCreateView):
    forced_job_type = ""

    def post(self, request, *args, **kwargs):
        return Response({"detail": "Job section endpoints are read-only."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class DailyWageJobsView(JobSectionView):
    forced_job_type = Task.JobType.DAILY_WAGE


class PartTimeJobsView(JobSectionView):
    forced_job_type = Task.JobType.PART_TIME


class WeekendJobsView(JobSectionView):
    forced_job_type = Task.JobType.WEEKEND


class EventJobsView(JobSectionView):
    forced_job_type = Task.JobType.EVENT


class FestivalJobsView(JobSectionView):
    forced_job_type = Task.JobType.FESTIVAL


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

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if request.user.role == User.Role.WORKER:
            from apps.search.services import record_task_event
            record_task_event(request.user, self.get_object(), "VIEW")
        return response


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


class TaskDecompositionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        task = generics.get_object_or_404(Task.objects.prefetch_related("skills"), pk=pk)
        if request.user.role == User.Role.ADMIN or task.owner_id == request.user.id:
            return Response(decompose_task(task))
        if request.user.role == User.Role.WORKER and task.status in (Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED):
            return Response(decompose_task(task))
        return Response({"detail": "You do not have access to this task."}, status=status.HTTP_403_FORBIDDEN)
