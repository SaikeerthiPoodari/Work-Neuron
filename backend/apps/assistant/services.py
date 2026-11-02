import json
import os
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment
from apps.notifications.models import Notification
from apps.tasks.models import Task

from .knowledge import KNOWLEDGE_VERSION, system_prompt

ROLE_LABELS = {User.Role.WORKER: "Worker", User.Role.CLIENT: "Client", User.Role.ADMIN: "Admin"}
STOP_WORDS = {"show", "find", "jobs", "near", "part", "time", "what", "how", "help", "latest", "active", "please", "naku", "naaku"}


class AssistantProvider:
    """Provider boundary; default mode is deterministic and offline."""

    def __init__(self):
        self.name = os.getenv("AI_PROVIDER", "fallback").strip().lower() or "fallback"
        self.configured = self.name in {"openai", "responses"} and bool(os.getenv("AI_API_KEY"))
        self.model = os.getenv("AI_MODEL", "gpt-6-luna")

    def answer(self, message, role, context):
        if not self.configured:
            return None
        user_content = [{"type": "input_text", "text": message}]
        user_content.extend({"type": "input_image", "image_url": item["data"]} for item in context.get("media", []))
        payload = {"model": self.model, "input": [
            {"role": "system", "content": system_prompt(role)},
            {"role": "system", "content": f"PREFERRED RESPONSE LANGUAGE: {context.get('language', 'auto')}. Follow it unless the user explicitly requests another language."},
            {"role": "system", "content": f"AUTHORIZED LIVE CONTEXT:\n{json.dumps(context.get('live', {}), ensure_ascii=False)}"},
            *[{"role": item.get("role", "user"), "content": str(item.get("content", ""))[:1000]} for item in context.get("history", [])[-8:]],
            {"role": "user", "content": user_content},
        ], "max_output_tokens": 700}
        request = Request(os.getenv("AI_API_URL", "https://api.openai.com/v1/responses"), data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {os.environ['AI_API_KEY']}", "Content-Type": "application/json"}, method="POST")
        for attempt in range(2):
            try:
                with urlopen(request, timeout=12) as response:
                    text = json.loads(response.read().decode()).get("output_text", "").strip()
                return text or None
            except (HTTPError, URLError, TimeoutError, ValueError):
                if attempt == 0:
                    time.sleep(0.15)
        return None


def _role_route(user, suffix):
    return f"/{user.role.lower()}/{suffix.lstrip('/')}"


def _live_context(user):
    data = {"role": user.role}
    if user.role == User.Role.WORKER:
        profile = getattr(user, "worker_profile", None)
        applications = Application.objects.filter(worker=user)
        data.update({"profile_complete": bool(profile and profile.headline and profile.location), "application_counts": {status: applications.filter(status=status).count() for status, _ in Application.Status.choices}, "assignment_count": Assignment.objects.filter(worker=user).count(), "unread_notifications": Notification.objects.filter(recipient=user, read_at__isnull=True).count()})
    elif user.role == User.Role.CLIENT:
        data.update({"owned_job_count": Task.objects.filter(owner=user).count(), "active_job_count": Task.objects.filter(owner=user, status__in=[Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED]).count(), "unread_notifications": Notification.objects.filter(recipient=user, read_at__isnull=True).count()})
    else:
        data.update({"unresolved_complaints": "available in protected admin control center", "unread_notifications": Notification.objects.filter(recipient=user, read_at__isnull=True).count()})
    return data


def _live_tasks(user, message):
    queryset = Task.objects.filter(status__in=[Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED]) if user.role == User.Role.WORKER else Task.objects.filter(owner=user)
    terms = [term for term in re.findall(r"[\w-]+", message.lower()) if len(term) > 2 and term not in STOP_WORDS]
    if terms:
        from django.db.models import Q
        query = Q()
        for term in terms[:5]:
            query |= Q(title__icontains=term) | Q(description__icontains=term) | Q(location__icontains=term) | Q(category__icontains=term)
        queryset = queryset.filter(query)
    return list(queryset.order_by("-created_at")[:5])


def _fallback(user, message, live, media=None):
    text = message.lower().strip()
    attachment_note = f" I received {len(media)} image attachment(s); image analysis requires the configured AI provider." if media else ""
    actions, suggestions = [], []
    if any(x in text for x in ("naaku", "ela", "endhuku", "kavali")):
        answer = "Mee WorkNeuron lo jobs kosam Tasks/Find Jobs open chesi filters use cheyyandi. Job detail open chesi requirements chusi Apply cheyyandi. Application status ni Applications lo track cheyyachu."
        actions.append({"label": "Open Find Jobs", "route": _role_route(user, "tasks")})
    elif any(x in text for x in ("mujhe", "kaise", "kahan")):
        answer = "WorkNeuron mein jobs ke liye Tasks, applications track karne ke liye Applications, aur profile badalne ke liye Profile > Edit Profile kholiye."
    elif user.role == User.Role.WORKER and any(x in text for x in ("job", "jobs", "near", "nearby", "recommend", "aply", "apply")):
        tasks = _live_tasks(user, message)
        answer = f"I found {len(tasks)} matching job result(s): {', '.join(task.title for task in tasks[:3])}. Open a result to review its requirements and apply." if tasks else "I couldn't find matching open jobs in the current WorkNeuron data. Try Nearby Jobs, a different category/location, or update your skills and availability."
        actions.append({"label": "Open Find Jobs", "route": _role_route(user, "tasks")})
        if "near" in text or "nearby" in text: actions.append({"label": "Open Nearby Jobs", "route": _role_route(user, "nearby")})
        suggestions = ["How do I track an application?", "Why am I not getting Smart Matches?"]
    elif any(x in text for x in ("application", "aplication", "applicant", "track")):
        answer = f"You have {sum(live.get('application_counts', {}).values())} application record(s). Workers can review their status from Applications; clients review applicants from Applications and can select a worker there." if user.role == User.Role.WORKER else "Open Applications to compare applicants for your jobs. Worker selection is a client action; workers can only view and manage their own applications."
        actions.append({"label": "Open Applications", "route": _role_route(user, "applications")})
    elif any(x in text for x in ("profile", "profle", "skill", "portfolio")):
        answer = "Update your profile with headline, location, availability, education, experience, languages, and skills. A complete profile improves Smart Matches; workers can also open their professional portfolio."
        actions.extend([{"label": "Open Profile", "route": _role_route(user, f"people/{user.id}")}, {"label": "Edit Profile", "route": _role_route(user, "profile/edit")}])
    elif any(x in text for x in ("pay", "payment", "earning", "earn", "escrow")):
        answer = "Open Payments for transaction history and status. Workers can also open Wallet for payout details. Assignment payments may remain pending or held in escrow until the relevant workflow releases them."
        actions.append({"label": "Open Payments", "route": _role_route(user, "payments")})
    elif any(x in text for x in ("post", "create", "publish")) and user.role == User.Role.CLIENT:
        answer = "Open Tasks and choose the create/post-job control. Add the title, requirements, budget, location, schedule, job type, and deadline before publishing."
        actions.append({"label": "Open Job Management", "route": _role_route(user, "tasks")})
    elif user.role == User.Role.ADMIN and any(x in text for x in ("stat", "fraud", "complaint", "report", "verification", "admin")):
        answer = "Those records are restricted to the Admin control center. Open it to review platform controls, complaints/reports, payments, and verification-related records."
        actions.append({"label": "Open Admin Control Center", "route": "/admin/admin"})
    elif any(x in text for x in ("complaint", "report", "scam", "fraud", "suspicious")):
        answer = "If a job or interaction seems suspicious, open Complaints, choose the relevant category/reason, describe what happened, and submit it. Nora cannot resolve reports or expose another user's private data."
        actions.append({"label": "Open Complaints", "route": _role_route(user, "complaints")})
    else:
        answer = f"I’m Nora, your WorkNeuron assistant for the {ROLE_LABELS.get(user.role, 'platform')} workspace. I can explain jobs, applications, profiles, Smart Matches, assignments, payments, complaints, notifications, networking, and role permissions using the current app."
        suggestions = ["Help me find jobs", "How do I update my profile?", "Where can I check payments?"]
    return {"message": answer + attachment_note, "suggestions": suggestions, "actions": actions}


def respond(user, message, context=None, media=None):
    context = context or {}
    provider = AssistantProvider()
    live = _live_context(user)
    generated = provider.answer(message, user.role, {**context, "live": live, "media": media or []})
    fallback = _fallback(user, message, live, media=media)
    result = {"message": generated, "suggestions": fallback["suggestions"], "actions": fallback["actions"]} if generated else fallback
    result.update({"provider": provider.name, "configured": provider.configured, "knowledge_version": KNOWLEDGE_VERSION})
    return result
