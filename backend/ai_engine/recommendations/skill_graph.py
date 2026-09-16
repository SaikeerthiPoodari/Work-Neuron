from collections import defaultdict

from apps.skills.models import Skill, WorkerSkill


def build_skill_graph():
    """Build an explainable skill co-occurrence graph from worker profiles.

    A node represents an active catalog skill. An edge connects two skills when
    at least one worker has selected both skills. Edge weight is the number of
    distinct workers sharing the pair; this makes the graph useful for
    discovery without claiming that skills are causally related.
    """
    skills = list(Skill.objects.filter(is_active=True).order_by("name"))
    worker_skills = WorkerSkill.objects.filter(
        skill__is_active=True,
        skill__in=skills,
    ).values_list("worker_id", "skill_id", "skill__name")

    names = {skill.id: skill.name for skill in skills}
    categories = {skill.id: skill.category for skill in skills}
    workers_by_skill = defaultdict(set)
    skills_by_worker = defaultdict(set)
    for worker_id, skill_id, _ in worker_skills:
        workers_by_skill[skill_id].add(worker_id)
        skills_by_worker[worker_id].add(skill_id)

    edge_workers = defaultdict(set)
    for worker_skill_ids in skills_by_worker.values():
        ordered_ids = sorted(worker_skill_ids)
        for index, source_id in enumerate(ordered_ids):
            for target_id in ordered_ids[index + 1 :]:
                edge_workers[(source_id, target_id)].update(
                    workers_by_skill[source_id].intersection(workers_by_skill[target_id])
                )

    nodes = [
        {
            "id": skill.id,
            "name": skill.name,
            "category": skill.category,
            "worker_count": len(workers_by_skill[skill.id]),
        }
        for skill in skills
    ]
    edges = [
        {
            "source": source_id,
            "target": target_id,
            "weight": len(worker_ids),
        }
        for (source_id, target_id), worker_ids in sorted(edge_workers.items())
        if worker_ids
    ]
    return {"nodes": nodes, "edges": edges}
