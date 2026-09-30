from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

from ai_engine.recommendations.skill_graph import build_skill_graph

from .models import Skill, WorkerSkill, WorkerSkillHistory
from .permissions import IsAdminRole, IsWorkerRole
from .serializers import SkillSerializer, WorkerSkillSerializer


class SkillListCreateView(generics.ListCreateAPIView):
    queryset = Skill.objects.filter(is_active=True)
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminRole()]
        return super().get_permissions()


class SkillDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAdminRole]


class MySkillsView(generics.ListCreateAPIView):
    serializer_class = WorkerSkillSerializer
    permission_classes = [IsWorkerRole]

    def get_queryset(self):
        return WorkerSkill.objects.filter(worker=self.request.user).select_related("skill")

    def perform_create(self, serializer):
        serializer.save(worker=self.request.user)


class MySkillDetailView(generics.DestroyAPIView):
    serializer_class = WorkerSkillSerializer
    permission_classes = [IsWorkerRole]

    def get_queryset(self):
        return WorkerSkill.objects.filter(worker=self.request.user)


class SkillGraphView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response(build_skill_graph())


class WorkerSkillProgressView(generics.GenericAPIView):
    permission_classes = [IsWorkerRole]

    def get(self, request, *args, **kwargs):
        period = request.query_params.get("period", "month")
        days = {"week": 7, "month": 30, "year": 365}.get(period)
        if not days:
            return Response({"detail": "period must be week, month, or year."}, status=status.HTTP_400_BAD_REQUEST)
        since = timezone.now() - timedelta(days=days)
        history = WorkerSkillHistory.objects.filter(worker=request.user, recorded_at__gte=since).select_related("skill")
        from apps.assignments.models import Assignment
        from apps.payments.models import Transaction
        assignments = Assignment.objects.filter(worker=request.user, task__status="COMPLETED", completed_at__gte=since).select_related("task").prefetch_related("task__skills")
        transactions = Transaction.objects.filter(assignment__worker=request.user, status=Transaction.Status.VERIFIED, created_at__gte=since).select_related("assignment__task", "payer")
        return Response({
            "period": period,
            "skill_history": [{"skill_id": row.skill_id, "skill_name": row.skill.name, "proficiency": row.proficiency, "years_experience": row.years_experience, "recorded_at": row.recorded_at} for row in history],
            "completed_tasks": [{"assignment_id": item.id, "task_title": item.task.title, "completed_at": item.completed_at, "skills": [skill.name for skill in item.task.skills.all()]} for item in assignments],
            "earnings": [{"transaction_id": item.id, "task_title": item.assignment.task.title, "amount": str(item.amount), "currency": item.currency, "created_at": item.created_at} for item in transactions],
            "summary": {"completed_tasks": assignments.count(), "verified_earnings": str(sum((item.amount for item in transactions), start=0))},
        })
