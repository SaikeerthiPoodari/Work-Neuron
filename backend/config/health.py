from django.db import connection
from django.http import JsonResponse
from django.views import View


class HealthView(View):
    """Small unauthenticated liveness/readiness probe for hosting platforms."""

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return JsonResponse({"status": "ok", "database": "ok"})
        except Exception:
            return JsonResponse({"status": "degraded", "database": "unavailable"}, status=503)
