from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import User
from apps.assignments.models import Assignment
from apps.tasks.models import Task


class SeedDemoCommandTests(TestCase):
    def test_command_creates_idempotent_presentation_data(self):
        output = StringIO()
        call_command("seed_demo", stdout=output)
        call_command("seed_demo", stdout=StringIO())

        self.assertIn("Demo data is ready.", output.getvalue())
        self.assertTrue(User.objects.filter(email="demo.client@workneuron.local").exists())
        self.assertGreaterEqual(Task.objects.count(), 4)
        self.assertGreaterEqual(Assignment.objects.count(), 2)

        expected = {
            "Hyderabad": 15, "Bengaluru": 8, "Pune": 6, "Chennai": 6, "Mumbai": 5,
            "Delhi": 5, "Kochi": 4, "Coimbatore": 4, "Gurugram": 4, "Noida": 4,
            "Kolkata": 4, "Visakhapatnam": 4, "Jaipur": 3, "Ahmedabad": 3,
            "Vijayawada": 3, "Lucknow": 3, "Indore": 3, "Bhubaneswar": 3,
            "Chandigarh": 3, "Guwahati": 3,
        }
        for city, count in expected.items():
            with self.subTest(city=city):
                self.assertEqual(Task.objects.filter(location_city=city).count(), count)
        hyderabad = Task.objects.filter(location_city="Hyderabad")
        self.assertEqual(hyderabad.values("location_area").distinct().count(), 15)
        self.assertEqual(hyderabad.exclude(latitude__isnull=True).exclude(longitude__isnull=True).count(), 15)
        self.assertEqual(hyderabad.values("latitude", "longitude").distinct().count(), 15)
        self.assertFalse(hyderabad.filter(location_state="").exists())
        self.assertFalse(hyderabad.filter(required_languages=[]).exists())
        self.assertTrue(Task.objects.filter(location_city="Hyderabad", skill_level="LEVEL_1").exists())
        self.assertTrue(Task.objects.filter(location_city="Hyderabad", skill_level="LEVEL_2").exists())
        self.assertTrue(Task.objects.filter(location_city="Hyderabad", skill_level="LEVEL_3").exists())
        self.assertTrue(Task.objects.filter(location_city="Hyderabad", skills__isnull=False).exists())
