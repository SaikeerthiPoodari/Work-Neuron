import os
import re

from apps.accounts.models import User
from apps.tasks.models import Task


ROLE_LABELS = {User.Role.WORKER: "Worker", User.Role.CLIENT: "Client", User.Role.ADMIN: "Admin"}


class AssistantProvider:
    """Provider boundary. External providers can be added without changing the API or RBAC layer."""

    def __init__(self):
        self.name = os.getenv("AI_PROVIDER", "fallback").strip().lower() or "fallback"
        self.configured = bool(os.getenv("AI_API_KEY")) if self.name not in {"", "fallback", "local"} else False

    def answer(self, message, role, context):
        # Deliberately keep the default provider local and deterministic. It never invents data.
        return None


def _role_route(user, suffix):
    return f"/{user.role.lower()}/{suffix.lstrip('/')}"


def _live_tasks(user, message):
    queryset = Task.objects.filter(status__in=[Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED]) if user.role == User.Role.WORKER else Task.objects.all()
    if user.role == User.Role.CLIENT:
        queryset = queryset.filter(owner=user)
    terms = [term for term in re.findall(r"[\w-]+", message.lower()) if len(term) > 2 and term not in {"show", "find", "jobs", "near", "part", "time", "what", "how", "help", "latest", "active"}]
    if terms:
        from django.db.models import Q
        query = Q()
        for term in terms[:5]:
            query |= Q(title__icontains=term) | Q(description__icontains=term) | Q(location__icontains=term)
        queryset = queryset.filter(query)
    return list(queryset.order_by("-created_at")[:5])


def respond(user, message, context=None):
    context = context or {}
    role = user.role
    provider = AssistantProvider()
    generated = provider.answer(message, role, context)
    if generated:
        return generated

    text = message.lower().strip()
    suggestions = []
    actions = []
    if any(word in text for word in ("job", "jobs", "near", "part-time", "part time", "recommend")) and role == User.Role.WORKER:
        tasks = _live_tasks(user, message)
        if tasks:
            names = ", ".join(task.title for task in tasks[:3])
            answer = f"I found {len(tasks)} available job result{'s' if len(tasks) != 1 else ''} from WorkNeuron: {names}. Open Jobs to review the complete details."
        else:
            answer = "I couldn't find matching available jobs in the current WorkNeuron data. Try adjusting the job type, location, or radius filters."
        actions.append({"label": "Open Jobs", "route": _role_route(user, "tasks")})
        suggestions = ["Show my applications", "Show my active tasks", "How do I improve my profile?"]
    elif any(word in text for word in ("post", "create", "publish")) and role == User.Role.CLIENT:
        answer = "You can create a job from the Tasks section. Add the role, requirements, budget, location, and schedule before publishing."
        actions.append({"label": "Open Post Job", "route": _role_route(user, "tasks")})
        suggestions = ["Show my active jobs", "Show pending applications", "How do I verify my business?"]
    elif any(word in text for word in ("application", "applicant")):
        answer = "Your applications workspace shows the current records available to your account. I can only return data authorized for your role."
        actions.append({"label": "Open Applications", "route": _role_route(user, "applications")})
        suggestions = ["Show active tasks", "Explain my recommendations"] if role == User.Role.WORKER else ["Find suitable workers", "Show selected workers"]
    elif any(word in text for word in ("verification", "verify")) and role == User.Role.CLIENT:
        answer = "Business verification is managed from your Verification section. Submit the requested business details and documents there."
        actions.append({"label": "Open Verification", "route": _role_route(user, "verification")})
    elif role == User.Role.ADMIN and any(word in text for word in ("stat", "user", "fraud", "complaint", "report", "verification")):
        answer = "Admin data is available in the protected control center. I can guide you there, while the backend continues to enforce admin permissions."
        actions.append({"label": "Open Admin Dashboard", "route": _role_route(user, "dashboard")})
    elif any(word in text for word in ("profile", "skill")):
        answer = "Keep your WorkNeuron profile current with your skills, experience, availability, and location so recommendations remain useful."
        actions.append({"label": "Open Profile", "route": _role_route(user, "profile")})
    elif any(word in text for word in ("task", "assignment", "payment", "earn")):
        answer = "Your role workspace contains the task, assignment, and payment information that your account is authorized to access."
        actions.append({"label": "Open Dashboard", "route": _role_route(user, "dashboard")})
    else:
        answer = f"I’m Nora, your WorkNeuron AI Assistant for the {ROLE_LABELS.get(role, 'platform')} workspace. I can help you navigate WorkNeuron and explain authorized jobs, tasks, applications, recommendations, profiles, payments, and verification."
        suggestions = ["Help me navigate WorkNeuron", "Show my dashboard", "What can you help with?"]
    return {"message": answer, "suggestions": suggestions, "actions": actions, "provider": provider.name, "configured": provider.configured}
