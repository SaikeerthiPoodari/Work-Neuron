from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tasks.models import Task
from ai_engine.embeddings.service import EmbeddingUnavailableError
from ai_engine.matching.scoring import score_worker_for_task


class TaskWorkerMatchesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        task = get_object_or_404(Task.objects.prefetch_related("skills"), pk=pk)
        if request.user.role not in (User.Role.ADMIN,) and task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner or an administrator can view worker matches."}, status=status.HTTP_403_FORBIDDEN)
        workers = User.objects.filter(role=User.Role.WORKER, is_active=True).prefetch_related("worker_skills__skill", "worker_profile")
        try:
            ranked = [{"worker": worker, "match": score_worker_for_task(task, worker)} for worker in workers]
        except EmbeddingUnavailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        ranked.sort(key=lambda item: item["match"]["overall_score"], reverse=True)
        return Response([{"worker": {**{key: value for key, value in {"id": item["worker"].id, "email": item["worker"].email, "first_name": item["worker"].first_name, "last_name": item["worker"].last_name, "role": item["worker"].role}.items()}}, "match": item["match"]} for item in ranked])

