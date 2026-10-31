from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("notifications", "0002_alter_notification_kind")]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="kind",
            field=models.CharField(
                choices=[
                    ("APPLICATION_RECEIVED", "Application received"),
                    ("APPLICATION_ACCEPTED", "Application accepted"),
                    ("APPLICATION_REJECTED", "Application rejected"),
                    ("APPLICATION_WITHDRAWN", "Application withdrawn"),
                    ("TASK_ASSIGNED", "Task assigned"),
                    ("TASK_STATUS_CHANGED", "Task status changed"),
                    ("TASK_SUBMITTED", "Task submitted"),
                    ("TASK_COMPLETED", "Task completed"),
                    ("REVIEW_RECEIVED", "Review received"),
                    ("PAYMENT_UPDATE", "Payment update"),
                    ("REPORT_RECEIVED", "Report received"),
                    ("VERIFICATION_UPDATE", "Verification update"),
                    ("MESSAGE_RECEIVED", "Message received"),
                    ("INTERVIEW_SCHEDULED", "Interview scheduled"),
                ],
                max_length=32,
            ),
        )
    ]
