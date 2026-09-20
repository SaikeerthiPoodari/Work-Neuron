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
