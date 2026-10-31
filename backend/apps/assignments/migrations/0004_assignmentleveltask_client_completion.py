from django.db import migrations, models
import django.conf


class Migration(migrations.Migration):
    dependencies = [("assignments", "0003_assignmentleveltask")]
    operations = [
        migrations.AddField(model_name="assignmentleveltask", name="client_completed", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="assignmentleveltask", name="client_completed_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="assignmentleveltask", name="client_completed_by", field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name="client_completed_assignment_tasks", to=django.conf.settings.AUTH_USER_MODEL)),
    ]
