from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User

from .services import parse_voice_query


class VoiceSearchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)

    def test_mixed_telugu_english_query_extracts_location_and_part_time(self):
        result = parse_voice_query("Naaku Hyderabad lo part-time job kavali")
        self.assertEqual(result["language"], "te-en")
        self.assertEqual(result["filters"], {"location": "Hyderabad", "job_type": "PART_TIME"})
        self.assertGreater(result["confidence"], 0.9)

    def test_english_query_extracts_location_and_daily_wage(self):
        result = parse_voice_query("I need a daily wage job in Hyderabad")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["filters"]["job_type"], "DAILY_WAGE")
        self.assertEqual(result["filters"]["location"], "Hyderabad")

    def test_voice_query_extracts_radius(self):
        result = parse_voice_query("Naaku Hyderabad lo 5 kilometers lopala part-time job kavali")
        self.assertEqual(result["filters"]["radius_km"], 5.0)

    def test_uninterpreted_query_does_not_guess(self):
        result = parse_voice_query("Please find something suitable")
        self.assertEqual(result["filters"], {})
        self.assertLess(result["confidence"], 0.5)

    def test_voice_api_requires_authentication(self):
        response = self.client.post(reverse("voice-search"), {"recognized_text": "part-time job in Hyderabad"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_voice_api_returns_structured_filters(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("voice-search"), {"recognized_text": "I need a weekend job in Hyderabad"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filters"]["job_type"], "WEEKEND")
