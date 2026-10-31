from django.db import connection
from django.conf import settings
from django.http import JsonResponse
from django.views import View


class HealthView(View):
    """Small unauthenticated liveness/readiness probe for hosting platforms."""

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return JsonResponse({"status": "degraded", "database": "unavailable", "realtime": "unknown"}, status=503)
        response = {"status": "ok", "database": "ok"}
        if settings.REDIS_URL:
            try:
                import redis
                redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2).ping()
                response["realtime"] = "redis"
            except Exception:
                return JsonResponse({"status": "degraded", "database": "ok", "realtime": "unavailable"}, status=503)
        else:
            response["realtime"] = "in_memory_development_only"
        return JsonResponse(response)
