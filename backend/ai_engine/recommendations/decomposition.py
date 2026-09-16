import re


def decompose_task(task):
    """Return transparent sentence-based steps and matched required skills."""
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", task.description.strip()) if part.strip()]
    required_skills = list(task.skills.filter(is_active=True).values("id", "name"))
    steps = []
    for index, sentence in enumerate(sentences, start=1):
        normalized = sentence.casefold()
        matched = [skill for skill in required_skills if skill["name"].casefold() in normalized]
        steps.append({"order": index, "description": sentence, "matched_skills": matched})
    return {
        "task_id": task.id,
        "method": "Sentence-based NLP decomposition with catalog-skill phrase matching",
        "steps": steps,
    }
