import re

from .models import SearchEvent


def record_task_event(user, task, kind):
    """Persist a minimal interaction signal; raw audio and sensitive data are never stored."""
    if user and task and kind in SearchEvent.Kind.values:
        SearchEvent.objects.create(user=user, task=task, kind=kind)


JOB_TYPES = {
    "part-time": "PART_TIME", "part time": "PART_TIME", "parttime": "PART_TIME",
    "full-time": "FULL_TIME", "full time": "FULL_TIME", "fulltime": "FULL_TIME",
    "daily wage": "DAILY_WAGE", "daily-wage": "DAILY_WAGE", "day wage": "DAILY_WAGE",
    "weekend": "WEEKEND", "event": "EVENT", "festival": "FESTIVAL", "internship": "INTERNSHIP",
    "freelance": "FREELANCE", "contract": "CONTRACT", "temporary": "TEMPORARY",
}
TELUGU_MARKERS = {"naaku", "kavali", "kaavali", "kosam", "lo", "undi"}
HINDI_MARKERS = {"mujhe", "chahiye", "mein", "ke", "liye", "naukri"}


def _language(text):
    if re.search(r"[\u0c00-\u0c7f]", text):
        return "te"
    if re.search(r"[\u0900-\u097f]", text):
        return "hi"
    words = set(re.findall(r"[a-z]+", text.lower()))
    if words & TELUGU_MARKERS:
        return "te-en"
    if words & HINDI_MARKERS:
        return "hi-en"
    return "en"


def _job_type(text):
    lowered = text.lower()
    for phrase, value in sorted(JOB_TYPES.items(), key=lambda item: -len(item[0])):
        if phrase in lowered:
            return value
    return ""


def _location(text):
    lowered = text.strip()
    patterns = [r"\b(?:in|near|at)\s+([A-Za-z][A-Za-z .-]{2,40}?)(?=\s+(?:for|with|as|job|work|part|full|daily|weekend|kavali)\b|[,\.!?]|$)", r"\b([A-Z][A-Za-z]{2,30})\s+lo\b"]
    for pattern in patterns:
        match = re.search(pattern, lowered, re.IGNORECASE if "lo" not in pattern else 0)
        if match:
            return match.group(1).strip(" .,-")
    return ""


def _radius(text):
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:km|kilometers?|kilometres?)", text.lower())
    return float(match.group(1)) if match else None


def parse_voice_query(text):
    text = " ".join((text or "").split())
    language = _language(text)
    job_type = _job_type(text)
    location = _location(text)
    radius = _radius(text)
    filters = {key: value for key, value in {"location": location, "job_type": job_type, "radius_km": radius}.items() if value is not None and value != ""}
    understood = len(filters)
    confidence = 0.95 if understood == 2 else 0.72 if understood == 1 else 0.15
    message = "Filters extracted. Review them before searching." if understood else "I couldn't fully understand your request. Please select or edit the search filters."
    return {"recognized_text": text, "language": language, "filters": filters, "confidence": confidence, "message": message}
