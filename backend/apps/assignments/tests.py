from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import Application
from apps.tasks.models import Task

from .models import Assignment, AssignmentLevel


class AssignmentApiTests(APITestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(email="client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.other_client = User.objects.create_user(email="other-client@example.com", password="secure-pass-123", role=User.Role.CLIENT)
        self.worker = User.objects.create_user(email="worker@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.other_worker = User.objects.create_user(email="other@example.com", password="secure-pass-123", role=User.Role.WORKER)
        self.task = Task.objects.create(owner=self.client_user, title="Implement service", description="Implement the service.", budget="1000.00", deadline=timezone.now() + timedelta(days=5), status=Task.Status.ASSIGNED)
        application = Application.objects.create(task=self.task, worker=self.worker, cover_letter="I can help.", status=Application.Status.ACCEPTED)
        self.assignment = Assignment.objects.create(task=self.task, worker=self.worker, application=application)

    def configure(self):
        self.client.force_authenticate(user=self.client_user)
        return self.client.put(reverse("assignment-levels-config", kwargs={"pk": self.assignment.id}), {"levels": [
            {"title": "Planning", "description": "Clarify the scope", "tasks": ["Review project brief", "Write implementation plan"], "deliverables": "Approved plan document", "required_materials": "Project brief", "requirements": "Provide the approved plan"},
            {"title": "Delivery", "description": "Build the solution", "tasks": ["Implement feature", "Prepare release notes"], "deliverables": "Working code and release notes", "required_materials": "Approved plan document", "requirements": "Provide working code"},
        ]}, format="json")

    def complete_checklist(self, level):
        for task in level["tasks"]:
            self.client.post(reverse("assignment-level-task-complete", kwargs={"pk": self.assignment.id, "level_id": level["id"], "task_id": task["id"]}))

    def test_worker_cannot_skip_locked_levels_and_client_review_unlocks_next(self):
        configured = self.configure()
        self.assertEqual(configured.status_code, status.HTTP_200_OK)
        self.assertEqual(configured.data["levels"][0]["deliverables"], "Approved plan document")
        self.assertEqual(configured.data["levels"][0]["required_materials"], "Project brief")
        self.assertEqual([task["title"] for task in configured.data["levels"][0]["tasks"]], ["Review project brief", "Write implementation plan"])
        self.client.force_authenticate(user=self.worker)
        started = self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        self.assertEqual(started.status_code, status.HTTP_200_OK)
        levels = started.data["levels"]
        self.assertEqual([level["status"] for level in levels], ["CURRENT", "LOCKED"])
        self.complete_checklist(levels[0])

        submit = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"submission": "Plan attached"}, format="json")
        self.assertEqual(submit.status_code, status.HTTP_200_OK)
        self.assertEqual([level["status"] for level in submit.data["levels"]], ["SUBMITTED", "LOCKED"])
        self.assertEqual(submit.data["progress"], 0)

        self.client.force_authenticate(user=self.other_worker)
        forbidden = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"submission": "wrong user"}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.other_client)
        forbidden = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"action": "approve"}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.client_user)
        review = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"action": "approve", "feedback": "Good plan"}, format="json")
        self.assertEqual(review.status_code, status.HTTP_200_OK)
        self.assertEqual([level["status"] for level in review.data["levels"]], ["COMPLETED", "CURRENT"])
        self.assertEqual(review.data["progress"], 50)

        self.client.force_authenticate(user=self.worker)
        dashboard = self.client.get(reverse("assignment-list"))
        self.assertEqual([level["status"] for level in dashboard.data[0]["levels"]], ["COMPLETED", "CURRENT"])
        self.assertEqual(dashboard.data[0]["progress"], 50)

    def test_rejection_keeps_current_level_unlocked_and_does_not_unlock_next(self):
        self.assertEqual(self.configure().status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.worker)
        started = self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        first = self.assignment.levels.get(order=1)
        self.complete_checklist(started.data["levels"][0])
        submitted = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": first.id}), {"submission": "Needs revision"}, format="json")
        self.assertEqual([level["status"] for level in submitted.data["levels"]], ["SUBMITTED", "LOCKED"])

        self.client.force_authenticate(user=self.client_user)
        rejected = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": first.id}), {"action": "reject", "feedback": "Please revise"}, format="json")
        self.assertEqual(rejected.status_code, status.HTTP_200_OK)
        self.assertEqual([level["status"] for level in rejected.data["levels"]], ["CURRENT", "LOCKED"])
        self.assertEqual(rejected.data["progress"], 0)
        self.assertEqual(rejected.data["levels"][0]["submission"], "Needs revision")

        self.client.force_authenticate(user=self.worker)
        resubmitted = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": first.id}), {"submission": "Revised and ready"}, format="json")
        self.assertEqual(resubmitted.status_code, status.HTTP_200_OK)
        self.assertEqual([level["status"] for level in resubmitted.data["levels"]], ["SUBMITTED", "LOCKED"])

    def test_three_levels_progress_only_after_each_client_approval(self):
        self.client.force_authenticate(user=self.client_user)
        configured = self.client.put(reverse("assignment-levels-config", kwargs={"pk": self.assignment.id}), {"levels": [
            {"title": "Work Delivery", "description": "Complete the first work stage.", "tasks": ["Prepare the first stage"], "deliverables": "First-stage output", "required_materials": "Project brief", "requirements": "Submit the first-stage output"},
            {"title": "Advanced Task", "description": "Complete the advanced work stage.", "tasks": ["Complete the advanced work"], "deliverables": "Advanced output", "required_materials": "Approved first-stage output", "requirements": "Submit the advanced output"},
            {"title": "Final Delivery", "description": "Prepare the final work stage.", "tasks": ["Prepare the final package"], "deliverables": "Final package", "required_materials": "Approved prior work", "requirements": "Submit the final package"},
        ]}, format="json")
        self.assertEqual(configured.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.worker)
        self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        levels = configured.data["levels"]
        self.complete_checklist(levels[0])

        first_submit = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"submission": "Level one"}, format="json")
        self.assertEqual([level["status"] for level in first_submit.data["levels"]], ["SUBMITTED", "LOCKED", "LOCKED"])
        self.assertEqual(first_submit.data["progress"], 0)
        self.client.force_authenticate(user=self.client_user)
        first_approval = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": levels[0]["id"]}), {"action": "approve"}, format="json")
        self.assertEqual([level["status"] for level in first_approval.data["levels"]], ["COMPLETED", "CURRENT", "LOCKED"])
        self.assertEqual(first_approval.data["progress"], 33)

        self.client.force_authenticate(user=self.worker)
        self.complete_checklist(levels[1])
        second_submit = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": levels[1]["id"]}), {"submission": "Level two"}, format="json")
        self.assertEqual([level["status"] for level in second_submit.data["levels"]], ["COMPLETED", "SUBMITTED", "LOCKED"])
        self.client.force_authenticate(user=self.client_user)
        second_approval = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": levels[1]["id"]}), {"action": "approve"}, format="json")
        self.assertEqual([level["status"] for level in second_approval.data["levels"]], ["COMPLETED", "COMPLETED", "CURRENT"])
        self.assertEqual(second_approval.data["progress"], 67)

        self.client.force_authenticate(user=self.worker)
        self.complete_checklist(levels[2])
        final_submit = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": levels[2]["id"]}), {"submission": "Final level"}, format="json")
        self.assertEqual(final_submit.data["task_status"], Task.Status.SUBMITTED)
        self.assertEqual(final_submit.data["progress"], 67)
        self.client.force_authenticate(user=self.client_user)
        final_approval = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": levels[2]["id"]}), {"action": "approve"}, format="json")
        self.assertEqual(final_approval.data["task_status"], Task.Status.COMPLETED)
        self.assertEqual(final_approval.data["progress"], 100)

    def test_final_stage_review_completes_task_and_assignment(self):
        self.assertEqual(self.configure().status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.worker)
        started = self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        first = self.assignment.levels.get(order=1)
        self.complete_checklist(started.data["levels"][0])
        self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": first.id}), {"submission": "Plan ready"}, format="json")
        self.client.force_authenticate(user=self.client_user)
        self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": first.id}), {"action": "approve"}, format="json")
        last = self.assignment.levels.get(order=2)
        self.client.force_authenticate(user=self.worker)
        self.complete_checklist(self.client.get(reverse("assignment-detail", kwargs={"pk": self.assignment.id})).data["levels"][1])
        submitted = self.client.post(reverse("assignment-level-submit", kwargs={"pk": self.assignment.id, "level_id": last.id}), {"submission": "Delivery ready"}, format="json")
        self.assertEqual(submitted.status_code, status.HTTP_200_OK)
        self.assertEqual(submitted.data["task_status"], Task.Status.SUBMITTED)
        self.client.force_authenticate(user=self.client_user)
        completed = self.client.post(reverse("assignment-level-review", kwargs={"pk": self.assignment.id, "level_id": last.id}), {"action": "approve", "feedback": "Accepted"}, format="json")
        self.assertEqual(completed.status_code, status.HTTP_200_OK)
        self.assertEqual(completed.data["progress"], 100)
        self.task.refresh_from_db()
        self.assignment.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.COMPLETED)
        self.assertIsNotNone(self.assignment.completed_at)

    def test_levels_can_only_be_configured_by_owner_before_start(self):
        self.client.force_authenticate(user=self.other_client)
        forbidden = self.client.put(reverse("assignment-levels-config", kwargs={"pk": self.assignment.id}), {"levels": [{"title": "Stage"}]}, format="json")
        self.assertEqual(forbidden.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.configure().status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.worker)
        self.client.post(reverse("assignment-start", kwargs={"pk": self.assignment.id}))
        self.client.force_authenticate(user=self.client_user)
        locked = self.client.put(reverse("assignment-levels-config", kwargs={"pk": self.assignment.id}), {"levels": [{"title": "Changed"}]}, format="json")
        self.assertEqual(locked.status_code, status.HTTP_400_BAD_REQUEST)
