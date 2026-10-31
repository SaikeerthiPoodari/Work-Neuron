from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from .health import HealthView


class HealthViewTests(TestCase):
    @override_settings(REDIS_URL="")
    def test_health_reports_local_realtime_fallback(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok", "realtime": "in_memory_development_only"})

    @override_settings(REDIS_URL="redis://redis.example:6379/0")
    @patch("redis.Redis.from_url")
    def test_health_pings_configured_redis(self, from_url):
        from_url.return_value = Mock()
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["realtime"], "redis")
        from_url.return_value.ping.assert_called_once_with()

    @override_settings(REDIS_URL="redis://redis.example:6379/0")
    @patch("redis.Redis.from_url")
    def test_health_returns_degraded_when_configured_redis_is_unavailable(self, from_url):
        from_url.return_value.ping.side_effect = OSError("redis unavailable")
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "degraded", "database": "ok", "realtime": "unavailable"})
