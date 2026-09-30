from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tasks.models import Task
from apps.assignments.models import Assignment
from apps.reviews.models import Review
from apps.reputation.models import ReputationScore
from ai_engine.embeddings.service import EmbeddingUnavailableError
from ai_engine.matching.scoring import score_worker_for_task

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
        from apps.search.services import record_task_event
        record_task_event(self.request.user, task, "APPLY")


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


class ApplicationComparisonView(APIView):
    """Compare active applicants using the existing task-worker matcher and real profile history."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        if request.user.role != User.Role.CLIENT:
            return Response({"detail": "Applicant comparison is available to clients only."}, status=status.HTTP_403_FORBIDDEN)

        # Scoping the lookup itself prevents clients from learning whether another client's task exists.
        task = get_object_or_404(Task.objects.prefetch_related("skills"), pk=task_id, owner=request.user)
        applications = list(
            Application.objects.filter(task=task, status__in=[Application.Status.SUBMITTED, Application.Status.ACCEPTED])
            .select_related("worker", "worker__worker_profile")
            .prefetch_related("worker__worker_skills__skill")
            .order_by("-created_at")
        )
        worker_ids = [application.worker_id for application in applications]

        ratings = {
            row["reviewed_user_id"]: row
            for row in Review.objects.filter(reviewed_user_id__in=worker_ids)
            .values("reviewed_user_id").annotate(average=Avg("rating"), count=Count("id"))
        }
        reputation_scores = dict(ReputationScore.objects.filter(user_id__in=worker_ids)
                                 .values_list("user_id", "score"))
        completed = {
            row["worker_id"]: row["count"]
            for row in Assignment.objects.filter(worker_id__in=worker_ids, task__status=Task.Status.COMPLETED)
            .values("worker_id").annotate(count=Count("id"))
        }
        relevant = {
            row["worker_id"]: row["count"]
            for row in Assignment.objects.filter(worker_id__in=worker_ids, task__status=Task.Status.COMPLETED,
                                                 task__category__iexact=task.category)
            .values("worker_id").annotate(count=Count("id"))
        } if task.category else {}

        required_skills = list(task.skills.values("id", "name"))
        has_required_skills = bool(required_skills)
        applicants = []
        for application in applications:
            worker = application.worker
            profile = getattr(worker, "worker_profile", None)
            worker_skill_records = list(worker.worker_skills.all())
            rating = ratings.get(worker.id)
            # Feed actual review and reputation aggregates into the same weighted matcher.
            # Its existing neutral default remains in effect when no such record exists.
            worker._matching_rating_score = float(rating["average"] * 20) if rating else 50.0
            worker._matching_reputation_score = float(reputation_scores.get(worker.id, 50.0))
            try:
                match = score_worker_for_task(task, worker)
            except EmbeddingUnavailableError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            skill_match = match["skill_score"] if has_required_skills else None
            components = {key: match[key] for key in (
                "semantic_score", "skill_score", "experience_score", "rating_score",
                "availability_score", "location_score", "reputation_score", "education_score",
                "interest_score", "job_type_score", "salary_score",
            )}
            if not has_required_skills:
                components["skill_score"] = None
            applicants.append({
                "application": {
                    "id": application.id,
                    "status": application.status,
                    "cover_letter": application.cover_letter,
                    "proposed_budget": str(application.proposed_budget) if application.proposed_budget is not None else None,
                    "created_at": application.created_at,
                },
                "worker": {
                    "id": worker.id,
                    "name": " ".join(value for value in [worker.first_name, worker.last_name] if value).strip() or "WorkNeuron worker",
                    "headline": profile.headline if profile else "",
                    "bio": profile.bio if profile else "",
                    "experience_years": profile.experience_years if profile else None,
                    "availability": profile.availability if profile else None,
                    "portfolio_url": profile.portfolio_url if profile else "",
                    "skills": [{"id": item.skill_id, "name": item.skill.name,
                                "proficiency": item.proficiency, "years_experience": item.years_experience}
                               for item in worker_skill_records],
                    "rating_average": round(float(rating["average"]), 2) if rating else None,
                    "rating_count": rating["count"] if rating else 0,
                    "completed_tasks": completed.get(worker.id, 0),
                    "relevant_completed_tasks": relevant.get(worker.id, 0),
                },
                "match": {
                    "skill_match": skill_match,
                    "overall_score": match["overall_score"],
                    "components": components,
                    "weights": match["weights"],
                    "explanation": match["explanation"],
                },
            })

        return Response({
            "task": {"id": task.id, "title": task.title, "category": task.category,
                     "status": task.status, "required_skills": required_skills},
            "applicants": applicants,
            "eligible_applicant_count": len(applicants),
            "score_method": "Existing WorkNeuron worker-task matching score; factors and configured weights are included per applicant.",
        })


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
