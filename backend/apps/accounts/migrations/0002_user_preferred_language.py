from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [migrations.AddField(
        model_name="user",
        name="preferred_language",
        field=models.CharField(choices=[("en", "English"), ("te", "Telugu"), ("hi", "Hindi"), ("ta", "Tamil"), ("kn", "Kannada"), ("ml", "Malayalam"), ("bn", "Bengali"), ("mr", "Marathi"), ("ur", "Urdu"), ("gu", "Gujarati"), ("pa", "Punjabi")], default="en", max_length=5),
    )]
