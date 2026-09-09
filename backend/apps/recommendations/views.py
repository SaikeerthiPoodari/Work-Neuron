from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tasks.models import Task
from ai_engine.embeddings.service import EmbeddingUnavailableError
from ai_engine.matching.scoring import score_task_for_worker


def task_summary(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "budget": str(task.budget),
        "deadline": task.deadline,
        "location": task.location,
        "status": task.status,
        "required_skills": [{"id": skill.id, "name": skill.name} for skill in task.skills.all()],
    }


class SmartTaskFeedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.WORKER:
            return Response({"detail": "Smart Task Feed is available to workers only."}, status=status.HTTP_403_FORBIDDEN)
        limit = min(max(int(request.query_params.get("limit", 20)), 1), 50)
        tasks = Task.objects.filter(status__in=[Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED]).exclude(owner=request.user).prefetch_related("skills")
        if request.query_params.get("skill"):
            tasks = tasks.filter(skills__id=request.query_params["skill"])
        if request.query_params.get("location"):
            tasks = tasks.filter(location__icontains=request.query_params["location"])
        if request.query_params.get("min_budget"):
            tasks = tasks.filter(budget__gte=request.query_params["min_budget"])
        if request.query_params.get("max_budget"):
            tasks = tasks.filter(budget__lte=request.query_params["max_budget"])
        try:
            ranked = [{"task": task_summary(task), "match": score_task_for_worker(task, request.user)} for task in tasks.distinct()]
        except EmbeddingUnavailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        ranked.sort(key=lambda item: item["match"]["overall_score"], reverse=True)
        return Response(ranked[:limit])


class WorkerRecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role not in (User.Role.CLIENT, User.Role.ADMIN):
            return Response({"detail": "Worker recommendations are available to clients and administrators."}, status=status.HTTP_403_FORBIDDEN)
        task_id = request.query_params.get("task")
        if not task_id:
            return Response({"detail": "The task query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        task = get_object_or_404(Task.objects.prefetch_related("skills"), pk=task_id)
        if request.user.role == User.Role.CLIENT and task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner can view worker recommendations."}, status=status.HTTP_403_FORBIDDEN)
        workers = User.objects.filter(role=User.Role.WORKER, is_active=True).prefetch_related("worker_skills__skill", "worker_profile")
        try:
            ranked = [{"worker": {"id": worker.id, "email": worker.email, "first_name": worker.first_name, "last_name": worker.last_name, "role": worker.role}, "match": score_task_for_worker(task, worker)} for worker in workers]
        except EmbeddingUnavailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        ranked.sort(key=lambda item: item["match"]["overall_score"], reverse=True)
        return Response(ranked[:50])

