from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("profiles", "0003_workerprofile_current_area_and_more")]

    operations = [
        migrations.AddField(
            model_name="workerprofile",
            name="profile_photo_url",
            field=models.URLField(blank=True),
        ),
    ]
