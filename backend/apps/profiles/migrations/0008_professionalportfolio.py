from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("profiles", "0007_clientprofile_profile_photo")]

    operations = [migrations.CreateModel(name="ProfessionalPortfolio", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("summary", models.TextField(blank=True)),
        ("generated_at", models.DateTimeField(blank=True, null=True)),
        ("source_assignment_count", models.PositiveIntegerField(default=0)),
        ("updated_at", models.DateTimeField(auto_now=True)),
        ("worker", models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="professional_portfolio", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ["-updated_at"]})]
