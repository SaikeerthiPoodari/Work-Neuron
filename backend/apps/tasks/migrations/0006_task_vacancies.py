from django.db import migrations, models
from django.core.validators import MinValueValidator


class Migration(migrations.Migration):
    dependencies = [("tasks", "0005_alter_task_status")]

    operations = [
        migrations.AddField(
            model_name="task",
            name="vacancies",
            field=models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)]),
        ),
    ]
