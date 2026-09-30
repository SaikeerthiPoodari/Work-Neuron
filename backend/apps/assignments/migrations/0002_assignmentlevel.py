from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


def preserve_existing_assignments(apps, schema_editor):
    Assignment = apps.get_model("assignments", "Assignment")
    AssignmentLevel = apps.get_model("assignments", "AssignmentLevel")
    for assignment in Assignment.objects.select_related("task").iterator():
        task_status = assignment.task.status
        if task_status == "COMPLETED":
            level_status = "COMPLETED"
        elif task_status == "SUBMITTED":
            level_status = "SUBMITTED"
        else:
            level_status = "CURRENT"
        AssignmentLevel.objects.create(
            assignment=assignment,
            order=1,
            title="Work delivery",
            description=assignment.task.description,
            requirements="Submit the agreed work and supporting details for client review.",
            status=level_status,
            submission=assignment.submission,
            feedback=assignment.client_feedback,
            submitted_at=assignment.submitted_at,
            reviewed_at=assignment.completed_at,
        )


class Migration(migrations.Migration):
    dependencies = [("assignments", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="AssignmentLevel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveSmallIntegerField()),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("requirements", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("LOCKED", "Locked"), ("CURRENT", "Current"), ("SUBMITTED", "Submitted"), ("COMPLETED", "Completed")], default="LOCKED", max_length=12)),
                ("submission", models.TextField(blank=True)),
                ("feedback", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="levels", to="assignments.assignment")),
            ],
            options={"ordering": ["order"]},
        ),
        migrations.AddConstraint(
            model_name="assignmentlevel",
            constraint=models.UniqueConstraint(fields=("assignment", "order"), name="unique_assignment_level_order"),
        ),
        migrations.RunPython(preserve_existing_assignments, migrations.RunPython.noop),
    ]
