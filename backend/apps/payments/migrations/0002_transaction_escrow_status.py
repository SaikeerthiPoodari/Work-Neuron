from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payments", "0001_initial")]
    operations = [migrations.AddField(model_name="transaction", name="escrow_status", field=models.CharField(choices=[("PENDING", "Awaiting payment"), ("HELD", "Held in escrow"), ("RELEASED", "Released to worker")], default="PENDING", max_length=10))]
