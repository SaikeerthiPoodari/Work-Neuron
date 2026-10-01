from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.applications.models import Application
from apps.assignments.models import Assignment, AssignmentLevel, AssignmentLevelTask
from apps.tasks.models import Task


ASSIGNMENT_DEMOS = (
    {
        "title": "Data Entry & Validation",
        "description": "Enter assigned customer information into the provided spreadsheet, validate every record, and submit an accurate final file.",
        "levels": (
            ("Data Collection", "Collect the assigned customer information.\nEnter the information accurately into the provided spreadsheet.\nCheck that all required fields are filled.", "Completed customer data spreadsheet."),
            ("Data Validation", "Check the entered data for duplicates.\nIdentify missing or incorrect information.\nCorrect the identified errors.", "Validated and corrected spreadsheet."),
            ("Final Data Submission", "Perform a final quality check.\nMake sure all required records are complete.\nSubmit the final validated spreadsheet.", "Final approved spreadsheet."),
        ),
    },
    {
        "title": "Website Content Update",
        "description": "Research client-provided information, prepare clear website-ready copy, and submit a polished content package.",
        "levels": (
            ("Content Research", "Research the information provided by the client.\nCollect relevant and accurate content.\nOrganize the information for the website.", "Content research document."),
            ("Content Preparation", "Convert the researched information into website-ready content.\nFormat headings, descriptions and sections.\nCheck grammar and consistency.", "Website-ready content document."),
            ("Final Content Submission", "Perform the final content review.\nApply the client's requirements.\nSubmit the final website content.", "Final content package."),
        ),
    },
    {
        "title": "Excel Sales Analysis",
        "description": "Prepare the provided sales dataset, analyze key performance and trends, and deliver a clear client-ready report.",
        "levels": (
            ("Data Preparation", "Review the provided sales dataset.\nClean missing and duplicate records.\nPrepare the dataset for analysis.", "Clean sales dataset."),
            ("Sales Analysis", "Calculate important sales metrics.\nIdentify trends and top-performing products.\nCreate appropriate charts.", "Sales analysis with charts."),
            ("Final Report", "Summarize the analysis findings.\nAdd key insights and conclusions.\nPrepare the final report for the client.", "Final sales analysis report."),
        ),
    },
)


class Command(BaseCommand):
    help = "Reset only the three local worker assignment demo records and their level data."

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            worker = User.objects.get(email="demo.worker@workneuron.local", role=User.Role.WORKER)
            client = User.objects.get(email="demo.client@workneuron.local", role=User.Role.CLIENT)
        except User.DoesNotExist as exc:
            raise CommandError("Run seed_demo first so the demo client and worker accounts exist.") from exc

        assignments = list(Assignment.objects.filter(worker=worker).select_related("task", "application").order_by("-id"))
        if len(assignments) != 3:
            raise CommandError(f"Expected exactly 3 existing demo assignments for {worker.email}; found {len(assignments)}. No data was changed.")

        for assignment, demo in zip(assignments, ASSIGNMENT_DEMOS):
            task = assignment.task
            task.owner = client
            task.title = demo["title"]
            task.description = demo["description"]
            task.status = Task.Status.ASSIGNED
            task.save(update_fields=["owner", "title", "description", "status", "updated_at"])
            if assignment.application.task_id != task.id:
                raise CommandError(f"Assignment {assignment.pk} has an application for another task.")
            if assignment.application.worker_id != worker.id:
                raise CommandError(f"Assignment {assignment.pk} is not associated with the demo worker.")
            if assignment.application.status != Application.Status.ACCEPTED:
                assignment.application.status = Application.Status.ACCEPTED
                assignment.application.save(update_fields=["status", "updated_at"])

            assignment.progress = 0
            assignment.submission = ""
            assignment.client_feedback = ""
            assignment.started_at = None
            assignment.submitted_at = None
            assignment.completed_at = None
            assignment.save(update_fields=["progress", "submission", "client_feedback", "started_at", "submitted_at", "completed_at", "updated_at"])

            assignment.levels.all().delete()
            for order, (title, description, deliverable) in enumerate(demo["levels"], start=1):
                level = AssignmentLevel.objects.create(
                    assignment=assignment,
                    order=order,
                    title=title,
                    description=description,
                    deliverables=deliverable,
                    required_materials="Client-provided source data and project instructions.",
                    requirements="Submit the completed deliverable for client approval.",
                    status=AssignmentLevel.Status.CURRENT if order == 1 else AssignmentLevel.Status.LOCKED,
                )
                AssignmentLevelTask.objects.bulk_create([
                    AssignmentLevelTask(level=level, title=step)
                    for step in description.splitlines()
                ])

        self.stdout.write(self.style.SUCCESS("Reset 3 assignment demos with 3 ordered levels each."))
