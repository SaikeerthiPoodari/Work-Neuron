from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tasks.models import Task

from .models import Application
from .permissions import IsWorkerRole
from .serializers import ApplicationActionSerializer, ApplicationSerializer
from .services import decide_application, submit_application, withdraw_application


class ApplicationListCreateView(generics.ListCreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Application.objects.select_related("task", "worker")
        user = self.request.user
        if user.role == User.Role.WORKER:
            return queryset.filter(worker=user)
        if user.role == User.Role.CLIENT:
            return queryset.filter(task__owner=user)
        return queryset

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsWorkerRole()]
        return super().get_permissions()

    @transaction.atomic
    def perform_create(self, serializer):
        task = serializer.validated_data["task"]
        application = serializer.save(worker=self.request.user)
        submit_application(application, self.request.user)


class ApplicationDetailView(generics.RetrieveAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Application.objects.select_related("task", "worker")
        user = self.request.user
        if user.role == User.Role.WORKER:
            return queryset.filter(worker=user)
        if user.role == User.Role.CLIENT:
            return queryset.filter(task__owner=user)
        return queryset


class ApplicationDecisionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        application = generics.get_object_or_404(Application.objects.select_related("task"), pk=pk)
        if request.user.role != User.Role.ADMIN and application.task.owner_id != request.user.id:
            return Response({"detail": "Only the task owner or an administrator can decide applications."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ApplicationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = decide_application(application, serializer.validated_data["action"])
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        application.refresh_from_db()
        if assignment:
            return Response({"application": ApplicationSerializer(application).data, "assignment_id": assignment.id}, status=status.HTTP_200_OK)
        return Response(ApplicationSerializer(application).data, status=status.HTTP_200_OK)


class ApplicationWithdrawView(APIView):
    permission_classes = [IsWorkerRole]

    def post(self, request, pk):
        application = generics.get_object_or_404(Application, pk=pk)
        try:
            withdraw_application(application, request.user)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ApplicationSerializer(application).data)
