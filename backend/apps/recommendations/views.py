from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.db.models.functions import Trim
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.tasks.models import Task
from apps.skills.models import WorkerSkill
from ai_engine.embeddings.service import EmbeddingUnavailableError
from ai_engine.matching.scoring import score_task_for_worker
from apps.search.models import SearchEvent


def task_summary(task):
    verification = getattr(task.owner, "employer_verification", None)
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "budget": str(task.budget),
        "deadline": task.deadline,
        "location": task.location,
        "location_city": task.location_city,
        "location_area": task.location_area,
        "location_state": task.location_state,
        "latitude": task.latitude,
        "longitude": task.longitude,
        "category": task.category,
        "skill_level": task.skill_level,
        "required_languages": task.required_languages,
        "job_type": task.job_type,
        "work_mode": task.work_mode,
        "working_hours": task.working_hours,
        "experience_requirement": task.experience_requirement,
        "education_requirement": task.education_requirement,
        "status": task.status,
        "required_skills": [{"id": skill.id, "name": skill.name} for skill in task.skills.all()],
        "employer_verification": {"status": verification.status, "badge_text": verification.badge_text} if verification else {"status": "UNVERIFIED", "badge_text": ""},
    }


def apply_history_signal(match, task, user):
    """Lightweight, explainable interaction boost; it is not presented as deep learning."""
    from django.db.models import Count
    signals = SearchEvent.objects.filter(user=user, task=task).values("kind").annotate(total=Count("id"))
    counts = {item["kind"]: item["total"] for item in signals}
    boost = min(12.0, counts.get(SearchEvent.Kind.COMPLETE, 0) * 4 + counts.get(SearchEvent.Kind.APPLY, 0) * 2 + counts.get(SearchEvent.Kind.VIEW, 0) * 0.5)
    if boost:
        match = {**match, "overall_score": round(min(100.0, float(match["overall_score"]) + boost), 2), "explanation": f"{match.get('explanation', '')} Personalised using your prior interaction history.".strip()}
    return match


class SmartTaskFeedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.WORKER:
            return Response({"detail": "Smart Task Feed is available to workers only."}, status=status.HTTP_403_FORBIDDEN)
        limit = min(max(int(request.query_params.get("limit", 20)), 1), 50)
        SearchEvent.objects.create(user=request.user, kind=SearchEvent.Kind.RECOMMENDATION)
        tasks = Task.objects.filter(status__in=[Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED]).exclude(owner=request.user).prefetch_related("skills")
        job_type = request.query_params.get("job_type")
        if job_type:
            valid_job_types = {choice for choice, _label in Task.JobType.choices}
            if job_type not in valid_job_types:
                return Response({"detail": "Select a valid job type."}, status=status.HTTP_400_BAD_REQUEST)
            tasks = tasks.filter(job_type=job_type)
        if request.query_params.get("category"):
            tasks = tasks.filter(category__iexact=request.query_params["category"].strip())
        if request.query_params.get("skill"):
            tasks = tasks.filter(skills__id=request.query_params["skill"])
        if request.query_params.get("location"):
            tasks = tasks.filter(location__icontains=request.query_params["location"])
        if request.query_params.get("min_budget"):
            tasks = tasks.filter(budget__gte=request.query_params["min_budget"])
        if request.query_params.get("max_budget"):
            tasks = tasks.filter(budget__lte=request.query_params["max_budget"])
        if request.query_params.get("verified") in {"1", "true", "True"}:
            tasks = tasks.filter(owner__employer_verification__status="VERIFIED")
        try:
            ranked = [{"task": task_summary(task), "match": apply_history_signal(score_task_for_worker(task, request.user), task, request.user)} for task in tasks.distinct()]
        except EmbeddingUnavailableError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        ranked.sort(key=lambda item: item["match"]["overall_score"], reverse=True)
        return Response(ranked[:limit])


class JobRecommendationsView(SmartTaskFeedView):
    """Personalized job feed using the same explainable scorer as Smart Task Feed."""

    def get(self, request):
        response = super().get(request)
        if response.status_code != status.HTTP_200_OK:
            return response
        return Response(response.data)


class WorkerSkillGapView(APIView):
    """Evidence-based skill analysis using the worker's catalog skills and live tasks."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.WORKER:
            return Response({"detail": "Skill gap analysis is available to workers only."}, status=status.HTTP_403_FORBIDDEN)

        task_pool = Task.objects.filter(status__in=[Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED])
        categories = []
        seen_categories = set()
        for value in task_pool.exclude(category="").annotate(normalized_category=Trim("category")).order_by().values_list("normalized_category", flat=True).distinct():
            normalized = value.strip()
            key = normalized.casefold()
            if normalized and key not in seen_categories:
                categories.append(normalized)
                seen_categories.add(key)
        category = (request.query_params.get("category") or "").strip()
        task_id = request.query_params.get("task")
        target_task = None
        if task_id:
            target_task = get_object_or_404(task_pool.prefetch_related("skills"), pk=task_id)
            category = category or target_task.category

        category_tasks = task_pool
        if category:
            category_tasks = category_tasks.annotate(normalized_category=Trim("category")).filter(normalized_category__iexact=category)
        category_tasks = category_tasks.select_related("owner").prefetch_related("skills").order_by("-created_at")

        task_options = [{"id": item.id, "title": item.title, "category": item.category}
                        for item in category_tasks[:100]]
        worker_skills = list(WorkerSkill.objects.filter(worker=request.user, skill__is_active=True)
                             .select_related("skill").order_by("skill__name"))
        current_ids = {item.skill_id for item in worker_skills}
        current_data = [{"id": item.skill_id, "name": item.skill.name,
                         "proficiency": item.proficiency, "years_experience": item.years_experience}
                        for item in worker_skills]

        result = {
            "categories": categories,
            "target_tasks": task_options,
            "current_skills": current_data,
            "target": {"category": category or None,
                       "task": {"id": target_task.id, "title": target_task.title} if target_task else None},
            "required_skills": [], "matched_skills": [], "missing_skills": [], "improve_skills": [],
            "match_percentage": 0, "matched_count": 0, "required_count": 0,
            "matching_task_count": category_tasks.count(),
            "data_available": False,
        }

        if not category and not target_task:
            result["message"] = "Choose a target category or task to compare your skills with current jobs."
            return Response(result)

        if target_task:
            required_ids = set(target_task.skills.filter(is_active=True).values_list("id", flat=True))
        else:
            required_ids = set()

        skill_rows = list(category_tasks.filter(skills__is_active=True)
                           .values("skills__id", "skills__name")
                           .annotate(task_count=Count("id", distinct=True))
                           .order_by("skills__name"))
        task_count = result["matching_task_count"]
        prevalence = {row["skills__id"]: row["task_count"] for row in skill_rows}
        if not target_task:
            required_ids = set(prevalence)

        required_skills = []
        for row in skill_rows:
            skill_id = row["skills__id"]
            if skill_id not in required_ids:
                continue
            appearances = prevalence[skill_id]
            frequency = round(appearances * 100 / task_count, 1) if task_count else 0
            priority = "high" if frequency >= 70 else "medium" if frequency >= 40 else "low"
            required_skills.append({"id": skill_id, "name": row["skills__name"],
                                    "task_count": appearances, "frequency_percent": frequency,
                                    "priority": priority})

        matched = [skill for skill in required_skills if skill["id"] in current_ids]
        missing = [skill for skill in required_skills if skill["id"] not in current_ids]
        current_by_id = {item["id"]: item for item in current_data}
        improve = [{**skill, "proficiency": current_by_id[skill["id"]]["proficiency"]}
                   for skill in matched if current_by_id[skill["id"]]["proficiency"] <= 2]
        required_count = len(required_skills)
        match_percentage = round(len(matched) * 100 / required_count) if required_count else 0
        result.update({"required_skills": required_skills, "matched_skills": matched,
                       "missing_skills": missing, "improve_skills": improve,
                       "match_percentage": match_percentage,
                       "matched_count": len(matched), "required_count": required_count,
                       "data_available": bool(required_count),
                       "matching_task_count": task_count})

        if not task_count or not required_count:
            result["message"] = "There is not enough active job skill data for this target yet."
            result["explanation"] = "Add skills to relevant job posts to make this analysis more useful."
        elif not current_data:
            result["message"] = "Add skills to your worker profile to see your match."
            result["explanation"] = f"This target is based on {task_count} active job{'s' if task_count != 1 else ''}; no current profile skills are listed yet."
        else:
            strongest = ", ".join(skill["name"] for skill in matched[:3]) or "none of the listed requirements yet"
            next_skill = missing[0] if missing else None
            result["explanation"] = f"Your strongest matching skills are {strongest}."
            if next_skill:
                result["explanation"] += f" {next_skill['name']} is a useful next skill because it appears in {next_skill['frequency_percent']}% of matching jobs."
            else:
                result["explanation"] += " You currently match every skill requirement in this target set."
        result["recommendations"] = ([{**skill, "action": "learn"} for skill in missing]
                                      + [{**skill, "action": "improve"} for skill in improve])[:5]
        return Response(result)


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
