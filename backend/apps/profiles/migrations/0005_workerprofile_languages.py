from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("profiles", "0004_workerprofile_profile_photo_url")]

    operations = [
        migrations.AddField(
            model_name="workerprofile",
            name="languages",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
