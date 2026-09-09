import json
import os

from sklearn.metrics.pairwise import cosine_similarity

from ai_engine.embeddings.service import SentenceEmbeddingService


DEFAULT_WEIGHTS = {
    "semantic": 0.45,
    "skill": 0.25,
    "experience": 0.10,
    "rating": 0.05,
    "availability": 0.05,
    "location": 0.05,
    "reputation": 0.05,
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
            skill_text,
        ]
    )
    return " ".join(profile_text.split())


def _task_text(task):
    return " ".join(
        " ".join([task.title, task.description, task.location, task.availability_requirements, " ".join(skill.name for skill in task.skills.all())]).split()
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
    experience_score = min(float(experience_years) / 5 * 100, 100)
    task_location = (task.location or "").strip().lower()
    worker_location = (getattr(profile, "location", "") or "").strip().lower() if profile else ""
    location_score = 100.0 if not task_location or task_location == "remote" or task_location == worker_location else 50.0
    availability_score = 100.0 if not task.availability_requirements else 50.0
    # Ratings/reputation are neutral until the review and reputation phases provide data.
    return {
        "skill": skill_score,
        "experience": experience_score,
        "rating": 50.0,
        "availability": availability_score,
        "location": location_score,
        "reputation": 50.0,
    }


def score_worker_for_task(task, worker, embedder=None):
    embedder = embedder or SentenceEmbeddingService()
    components = _structured_scores(task, worker)
    components["semantic"] = _semantic_score(_task_text(task), _worker_text(worker), embedder)
    weights = matching_weights()
    overall = sum(components[key] * weights[key] for key in weights)
    required_names = {name.lower() for name in task.skills.values_list("name", flat=True)}
    worker_names = {name.lower() for name in worker.worker_skills.select_related("skill").values_list("skill__name", flat=True)}
    overlap = sorted(required_names & worker_names)
    display_names = {skill.name.lower(): skill.name for skill in task.skills.all()}
    if overlap:
        explanation = f"Strong match because the worker has relevant skills: {', '.join(display_names[name] for name in overlap)}."
    elif components["semantic"] >= 70:
        explanation = "Strong semantic similarity between the worker profile and task requirements."
    else:
        explanation = "Partial match; review the component scores before selecting this worker."
    return {
        "overall_score": round(overall, 2),
        "skill_score": round(components["skill"], 2),
        "semantic_score": round(components["semantic"], 2),
        "experience_score": round(components["experience"], 2),
        "rating_score": round(components["rating"], 2),
        "availability_score": round(components["availability"], 2),
        "location_score": round(components["location"], 2),
        "reputation_score": round(components["reputation"], 2),
        "weights": weights,
        "explanation": explanation,
    }


def score_task_for_worker(task, worker, embedder=None):
    return score_worker_for_task(task, worker, embedder=embedder)
