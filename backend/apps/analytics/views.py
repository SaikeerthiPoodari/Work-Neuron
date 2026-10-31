from datetime import date, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment
from apps.complaints.models import Complaint
from apps.fraud.models import FraudAlert
from apps.payments.models import Transaction
from apps.reviews.models import Review
from apps.tasks.models import Task
from apps.search.models import SearchEvent


PERIOD_DAYS = {"7d": 7, "30d": 30, "3m": 90, "6m": 180, "1y": 365}


def daily_counts(queryset, field, start, end, filters=None):
    """Aggregate dated records in SQL and fill missing calendar days for charts."""
    qs = queryset.filter(**{f"{field}__gte": start, f"{field}__lt": end})
    if filters:
        qs = qs.filter(**filters)
    rows = qs.annotate(day=TruncDate(field)).values("day").annotate(count=Count("id"))
    counts = {row["day"]: row["count"] for row in rows}
    result = []
    day = start.date()
    last_day = (end - timedelta(microseconds=1)).date()
    while day <= last_day:
        result.append({"date": day.isoformat(), "count": counts.get(day, 0)})
        day += timedelta(days=1)
    return result


class AnalyticsSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "Administrator privileges are required."}, status=403)

        period = request.query_params.get("range", "30d")
        if period not in PERIOD_DAYS:
            return Response({"range": "Use one of: 7d, 30d, 3m, 6m, 1y."}, status=400)

        now = timezone.now()
        start = now - timedelta(days=PERIOD_DAYS[period])
        previous_start = start - (now - start)

        users = User.objects.all()
        tasks = Task.objects.all()
        applications = Application.objects.all()
        assignments = Assignment.objects.all()
        transactions = Transaction.objects.all()

        def created_in(queryset, field="created_at", since=start, until=now):
            return queryset.filter(**{f"{field}__gte": since, f"{field}__lt": until})

        def count_change(queryset, field="created_at"):
            current = created_in(queryset, field).count()
            previous = created_in(queryset, field, previous_start, start).count()
            change = round((current - previous) * 100 / previous, 1) if previous else (100.0 if current else 0.0)
            return {"current": current, "previous": previous, "change_percent": change}

        user_counts = {
            "total": users.count(),
            "active": users.filter(is_active=True).count(),
            "clients": users.filter(role=User.Role.CLIENT).count(),
            "workers": users.filter(role=User.Role.WORKER).count(),
            "admins": users.filter(role=User.Role.ADMIN).count(),
        }
        task_status = {status: tasks.filter(status=status).count() for status, _ in Task.Status.choices}
        app_status = {status: applications.filter(status=status).count() for status, _ in Application.Status.choices}
        assignment_completed = assignments.filter(completed_at__isnull=False)
        transaction_verified = transactions.filter(status=Transaction.Status.VERIFIED)

        user_series = {
            "users": daily_counts(users, "date_joined", start, now),
            "workers": daily_counts(users, "date_joined", start, now, {"role": User.Role.WORKER}),
            "clients": daily_counts(users, "date_joined", start, now, {"role": User.Role.CLIENT}),
        }
        tasks_posted = daily_counts(tasks, "created_at", start, now)
        task_completion_rows = assignment_completed.filter(completed_at__gte=start, completed_at__lt=now).annotate(
            day=TruncDate("completed_at")
        ).values("day").annotate(count=Count("id"))
        task_completion_map = {row["day"]: row["count"] for row in task_completion_rows}
        task_completion_series = []
        for item in tasks_posted:
            task_completion_series.append({"date": item["date"], "posted": item["count"], "completed": task_completion_map.get(date.fromisoformat(item["date"]), 0)})

        app_series = daily_counts(applications, "created_at", start, now)
        transaction_rows = transaction_verified.filter(created_at__gte=start, created_at__lt=now).annotate(
            day=TruncDate("created_at")
        ).values("day").annotate(amount=Sum("amount"))
        transaction_map = {row["day"]: row["amount"] for row in transaction_rows}
        revenue_series = [{"date": item["date"], "amount": str(transaction_map.get(date.fromisoformat(item["date"]), 0) or 0)} for item in tasks_posted]

        period_applications = created_in(applications)
        period_accepted = period_applications.filter(status=Application.Status.ACCEPTED).count()
        application_total = period_applications.count()
        period_tasks = created_in(tasks)
        completed_period = period_tasks.filter(status=Task.Status.COMPLETED).count()
        completed_assignments_period = created_in(assignment_completed, "completed_at").count()
        period_transactions = created_in(transactions)
        verified_period = period_transactions.filter(status=Transaction.Status.VERIFIED)

        return Response({
            "range": period,
            "period": {"start": start.date().isoformat(), "end": now.date().isoformat()},
            "users": {**user_counts, "growth": user_series, "new": {
                "users": count_change(users, "date_joined"),
                "workers": count_change(users.filter(role=User.Role.WORKER), "date_joined"),
                "clients": count_change(users.filter(role=User.Role.CLIENT), "date_joined"),
            }},
            "tasks": {"total": tasks.count(), "by_status": task_status,
                "period_posted": period_tasks.count(), "period_completed": completed_period,
                "completion_rate": round(completed_period * 100 / period_tasks.count(), 1) if period_tasks.exists() else 0,
                "trend": task_completion_series},
            "applications": {"total": applications.count(), "by_status": app_status,
                "period_total": application_total,
                "period_accepted": period_accepted,
                "period_rejected": period_applications.filter(status=Application.Status.REJECTED).count(),
                "period_pending": period_applications.filter(status=Application.Status.SUBMITTED).count(),
                "acceptance_rate": round(period_accepted * 100 / application_total, 1) if application_total else 0,
                "trend": app_series},
            "assignments": {"total": assignments.count(), "completed": assignments.filter(task__status=Task.Status.COMPLETED).count()},
            "transactions": {"total": transactions.count(), "verified": transaction_verified.count(),
                "pending": transactions.filter(status=Transaction.Status.CREATED).count(),
                "verified_amount": str(transaction_verified.aggregate(total=Sum("amount"))["total"] or 0),
                "period_verified": verified_period.count(),
                "period_amount": str(verified_period.aggregate(total=Sum("amount"))["total"] or 0),
                "trend": revenue_series},
            "activity": {"active_users": user_counts["active"],
                "completed_assignments": completed_assignments_period,
                "reviews": created_in(Review.objects.all()).count(),
                "complaints": created_in(Complaint.objects.all()).count(),
                "fraud_alerts": created_in(FraudAlert.objects.all()).count()},
            "reviews": Review.objects.count(),
            "complaints": {"total": Complaint.objects.count(), "open": Complaint.objects.filter(status=Complaint.Status.OPEN).count()},
            "fraud_alerts": {"total": FraudAlert.objects.count(), "open": FraudAlert.objects.filter(status=FraudAlert.Status.OPEN).count()},
            "search_activity": {
                "voice_searches": SearchEvent.objects.filter(kind=SearchEvent.Kind.VOICE).count(),
                "recommendation_requests": SearchEvent.objects.filter(kind=SearchEvent.Kind.RECOMMENDATION).count(),
            },
        })


class ClientAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.CLIENT:
            return Response({"detail": "Client analytics are available to employers only."}, status=403)
        owned_tasks = Task.objects.filter(owner=request.user)
        owned_apps = Application.objects.filter(task__owner=request.user)
        owned_assignments = Assignment.objects.filter(task__owner=request.user)
        owned_transactions = Transaction.objects.filter(assignment__task__owner=request.user)
        accepted = owned_apps.filter(status=Application.Status.ACCEPTED).count()
        task_series = list(owned_tasks.values("status").annotate(count=Count("id")).order_by("status"))
        application_series = list(owned_apps.values("status").annotate(count=Count("id")).order_by("status"))
        payment_series = list(owned_transactions.values("status").annotate(total=Sum("amount"), count=Count("id")).order_by("status"))
        category_series = list(owned_tasks.exclude(category="").values("category").annotate(count=Count("id")).order_by("-count")[:8])
        location_series = list(owned_tasks.exclude(location_city="").values("location_city").annotate(count=Count("id")).order_by("-count")[:8])
        monthly_apps = list(owned_apps.annotate(period=TruncMonth("created_at")).values("period").annotate(count=Count("id")).order_by("period"))
        return Response({
            "jobs": {"total": owned_tasks.count(), "open": owned_tasks.filter(status__in=[Task.Status.OPEN, Task.Status.APPLICATIONS_RECEIVED]).count(), "completed": owned_tasks.filter(status=Task.Status.COMPLETED).count()},
            "applications": {"total": owned_apps.count(), "accepted": accepted, "pending": owned_apps.filter(status=Application.Status.SUBMITTED).count(), "acceptance_rate": round(accepted * 100 / owned_apps.count(), 1) if owned_apps.exists() else 0},
            "assignments": {"total": owned_assignments.count(), "completed": owned_assignments.filter(task__status=Task.Status.COMPLETED).count()},
            "payments": {"total": str(owned_transactions.filter(status=Transaction.Status.VERIFIED).exclude(escrow_status=Transaction.EscrowStatus.HELD).aggregate(total=Sum("amount"))["total"] or 0), "pending": str(owned_transactions.filter(escrow_status=Transaction.EscrowStatus.HELD).aggregate(total=Sum("amount"))["total"] or 0)},
            "series": {"tasks": task_series, "applications": application_series, "payments": [{**item, "total": str(item["total"] or 0)} for item in payment_series], "categories": category_series, "locations": location_series, "monthly_applications": [{"period": item["period"].date().isoformat(), "count": item["count"]} for item in monthly_apps]},
        })
