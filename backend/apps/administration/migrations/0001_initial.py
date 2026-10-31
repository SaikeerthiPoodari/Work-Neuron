import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=80)),
                ("target_type", models.CharField(max_length=80)),
                ("target_id", models.CharField(max_length=80)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="admin_audit_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "indexes": [models.Index(fields=["created_at"], name="administrat_created_e5a72d_idx"), models.Index(fields=["target_type", "target_id"], name="administrat_target__d6bf0b_idx")]},
        )
    ]
