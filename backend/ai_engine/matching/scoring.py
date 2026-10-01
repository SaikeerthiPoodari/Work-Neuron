import json
import os
import re
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from sklearn.metrics.pairwise import cosine_similarity

from ai_engine.embeddings.service import EmbeddingUnavailableError, SentenceEmbeddingService
from apps.profiles.languages import LANGUAGE_LABELS


DEFAULT_WEIGHTS = {
    "semantic": 0.45,
    "skill": 0.25,
    "category": 0.05,
    "experience": 0.10,
    "rating": 0.05,
    "availability": 0.05,
    "location": 0.05,
    "reputation": 0.05,
    "education": 0.03,
    "interest": 0.02,
    "job_type": 0.03,
    "salary": 0.02,
}


def matching_weights():
    raw = os.getenv("MATCHING_WEIGHTS_JSON")
    if not raw:
        return DEFAULT_WEIGHTS.copy()
    try:
        configured = json.loads(raw)
        weights = {key: float(configured.get(key, default)) for key, default in DEFAULT_WEIGHTS.items()}
        total = sum(value for value in weights.values() if value >= 0)
        if total <= 0:
            return DEFAULT_WEIGHTS.copy()
        return {key: max(value, 0) / total for key, value in weights.items()}
    except (TypeError, ValueError, json.JSONDecodeError):
        return DEFAULT_WEIGHTS.copy()


def _worker_text(worker):
    profile = getattr(worker, "worker_profile", None)
    skills = list(worker.worker_skills.select_related("skill").all())
    skill_text = ", ".join(item.skill.name for item in skills)
    profile_text = " ".join(
        [
            getattr(profile, "headline", "") if profile else "",
            getattr(profile, "bio", "") if profile else "",
            getattr(profile, "location", "") if profile else "",
            getattr(profile, "education", "") if profile else "",
            getattr(profile, "interests", "") if profile else "",
            ", ".join(LANGUAGE_LABELS.get(code, code) for code in getattr(profile, "languages", [])) if profile else "",
            getattr(profile, "preferred_working_hours", "") if profile else "",
            skill_text,
        ]
    )
    return " ".join(profile_text.split())


def _task_text(task):
    return " ".join(
        " ".join([task.title, task.description, task.category, task.job_type, task.education_requirement, task.experience_requirement, task.location, getattr(task, "location_city", ""), getattr(task, "location_area", ""), getattr(task, "work_mode", ""), task.working_hours, task.availability_requirements, " ".join(skill.name for skill in task.skills.all())]).split()
    )


def _semantic_score(task_text, worker_text, embedder):
    embeddings = embedder.encode([task_text, worker_text])
    similarity = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
    return max(0.0, min(100.0, ((similarity + 1) / 2) * 100))


def _structured_scores(task, worker):
    required_ids = set(task.skills.values_list("id", flat=True))
    worker_skills = list(worker.worker_skills.select_related("skill").all())
    worker_ids = {item.skill_id for item in worker_skills}
    skill_score = 50.0 if not required_ids else (len(required_ids & worker_ids) / len(required_ids)) * 100
    profile = getattr(worker, "worker_profile", None)
    experience_years = getattr(profile, "experience_years", 0) if profile else 0
    experience_text = (getattr(task, "experience_requirement", "") or "").lower()
    requested_years = [int(value) for value in re.findall(r"(\d+)\s*\+?\s*(?:years?|yrs?)", experience_text)]
    if requested_years:
        experience_score = 100.0 if experience_years >= min(requested_years) else max(20.0, experience_years / min(requested_years) * 100)
    elif experience_text and any(token in experience_text for token in ("experienced", "senior", "expert")):
        experience_score = min(float(experience_years) / 5 * 100, 100)
    else:
        experience_score = 100.0
    task_location = " ".join([task.location or "", getattr(task, "location_city", ""), getattr(task, "location_area", ""), getattr(task, "location_state", "")]).strip().lower()
    worker_location = " ".join([getattr(profile, "location", "") or "", getattr(profile, "current_city", "") or "", getattr(profile, "current_area", "") or "", getattr(profile, "current_state", "") or ""]).strip().lower() if profile else ""
    work_mode = getattr(task, "work_mode", "REMOTE")
    remote_preference = getattr(profile, "remote_preference", "ANY") if profile else "ANY"
    if work_mode == "REMOTE" or remote_preference == "REMOTE" and work_mode == "REMOTE":
        location_score = 100.0
    elif remote_preference not in ("ANY", work_mode) and work_mode != "HYBRID":
        location_score = 35.0
    elif task_location and worker_location and any(token in worker_location for token in task_location.split() if len(token) > 2):
        location_score = 100.0
    elif getattr(task, "latitude", None) is not None and getattr(task, "longitude", None) is not None and profile and profile.latitude is not None and profile.longitude is not None:
        d_lat, d_lon = radians(float(task.latitude) - float(profile.latitude)), radians(float(task.longitude) - float(profile.longitude))
        value = sin(d_lat / 2) ** 2 + cos(radians(float(profile.latitude))) * cos(radians(float(task.latitude))) * sin(d_lon / 2) ** 2
        distance = 6371 * 2 * asin(sqrt(value))
        radius = float(getattr(profile, "preferred_radius_km", 25) or 25)
        location_score = 100.0 if distance <= radius else max(20.0, 100.0 - ((distance - radius) / max(radius, 1)) * 50)
    else:
        location_score = 50.0 if task_location else 80.0
    required_hours = " ".join([getattr(task, "availability_requirements", "") or "", getattr(task, "working_hours", "") or ""]).lower()
    worker_schedule = " ".join([getattr(profile, "availability", "") or "", getattr(profile, "preferred_working_hours", "") or ""]).replace("_", " ").lower() if profile else ""
    if not required_hours:
        availability_score = 100.0
    elif worker_schedule and any(token in worker_schedule for token in ("flexible", "any")):
        availability_score = 90.0
    elif worker_schedule and any(token in worker_schedule for token in required_hours.split() if len(token) > 3):
        availability_score = 100.0
    else:
        availability_score = 40.0
    education = (getattr(profile, "education", "") or "").lower() if profile else ""
    required_education = (task.education_requirement or "").lower()
    education_score = 100.0 if not required_education or (education and any(token in education for token in required_education.split())) else 35.0
    interests = (getattr(profile, "interests", "") or "").lower() if profile else ""
    interest_score = 100.0 if not task.category or (interests and task.category.lower() in interests) else 50.0
    category = (getattr(task, "category", "") or "").strip().lower()
    profile_category_text = " ".join([getattr(profile, "headline", "") or "", interests, getattr(profile, "bio", "") or ""]).lower() if profile else ""
    category_score = 100.0 if not category or category in profile_category_text else 50.0
    preferred_type = (getattr(profile, "preferred_job_type", "") or "").lower() if profile else ""
    job_type_score = 100.0 if not preferred_type or preferred_type == task.job_type.lower() else 45.0
    preferred_salary = getattr(profile, "preferred_salary", None) if profile else None
    preferred_salary = Decimal(str(preferred_salary)) if preferred_salary else None
    task_budget = Decimal(str(task.budget))
    salary_score = 100.0 if not preferred_salary or task_budget >= preferred_salary else max(20.0, float(task_budget / preferred_salary * 100))
    # Callers may attach aggregated hiring context without changing default feed scores.
    rating_score = float(getattr(worker, "_matching_rating_score", 50.0))
    reputation_score = float(getattr(worker, "_matching_reputation_score", 50.0))
    return {
        "skill": skill_score,
        "category": category_score,
        "experience": experience_score,
        "rating": max(0.0, min(100.0, rating_score)),
        "availability": availability_score,
        "location": location_score,
        "reputation": max(0.0, min(100.0, reputation_score)),
        "education": education_score,
        "interest": interest_score,
        "job_type": job_type_score,
        "salary": salary_score,
    }


def score_worker_for_task(task, worker, embedder=None):
    embedder = embedder or SentenceEmbeddingService()
    components = _structured_scores(task, worker)
    semantic_available = True
    try:
        components["semantic"] = _semantic_score(_task_text(task), _worker_text(worker), embedder)
    except EmbeddingUnavailableError:
        # Keep recommendations available using the existing structured signals
        # when the optional local semantic model is not installed.
        components["semantic"] = 50.0
        semantic_available = False
    weights = matching_weights()
    overall = sum(components[key] * weights[key] for key in weights)
    required_names = {name.lower() for name in task.skills.values_list("name", flat=True)}
    worker_names = {name.lower() for name in worker.worker_skills.select_related("skill").values_list("skill__name", flat=True)}
    overlap = sorted(required_names & worker_names)
    display_names = {skill.name.lower(): skill.name for skill in task.skills.all()}
    reasons = []
    if overlap:
        reasons.append(f"relevant skills: {', '.join(display_names[name] for name in overlap)}")
    if getattr(task, "category", "") and components["category"] >= 80:
        reasons.append(f"category aligns with {task.category}")
    if task.experience_requirement and components["experience"] >= 80:
        reasons.append("experience meets the stated requirement")
    if (getattr(task, "working_hours", "") or getattr(task, "availability_requirements", "")) and components["availability"] >= 80:
        reasons.append("schedule aligns with your availability")
    if components["education"] >= 80 and task.education_requirement:
        reasons.append("education requirement alignment")
    if components["job_type"] >= 80 and getattr(getattr(worker, "worker_profile", None), "preferred_job_type", ""):
        reasons.append("preferred job type alignment")
    if components["salary"] >= 80 and getattr(getattr(worker, "worker_profile", None), "preferred_salary", None):
        reasons.append("budget preference alignment")
    if reasons:
        explanation = f"Recommended because it matches {', '.join(reasons)}."
    elif components["semantic"] >= 70:
        explanation = "Strong semantic similarity between the worker profile and task requirements."
    else:
        explanation = "Partial match; review the component scores before selecting this worker."
    if not semantic_available:
        explanation = f"{explanation} Semantic model unavailable; ranked using profile and job factors."
    return {
        "overall_score": round(overall, 2),
        "skill_score": round(components["skill"], 2),
        "category_score": round(components["category"], 2),
        "semantic_score": round(components["semantic"], 2),
        "experience_score": round(components["experience"], 2),
        "rating_score": round(components["rating"], 2),
        "availability_score": round(components["availability"], 2),
        "location_score": round(components["location"], 2),
        "reputation_score": round(components["reputation"], 2),
        "education_score": round(components["education"], 2),
        "interest_score": round(components["interest"], 2),
        "job_type_score": round(components["job_type"], 2),
        "salary_score": round(components["salary"], 2),
        "weights": weights,
        "explanation": explanation,
    }


def score_task_for_worker(task, worker, embedder=None):
    return score_worker_for_task(task, worker, embedder=embedder)
