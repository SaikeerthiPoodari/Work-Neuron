from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Skill, WorkerSkill
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

