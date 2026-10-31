from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("profiles", "0009_clientprofile_cover_image_workerprofile_cover_image")]
    operations = [
        migrations.AddField(model_name="clientprofile", name="bank_account_name", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="clientprofile", name="bank_account_number", field=models.CharField(blank=True, max_length=34)),
        migrations.AddField(model_name="clientprofile", name="bank_ifsc", field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name="clientprofile", name="upi_id", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="workerprofile", name="bank_account_name", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="workerprofile", name="bank_account_number", field=models.CharField(blank=True, max_length=34)),
        migrations.AddField(model_name="workerprofile", name="bank_ifsc", field=models.CharField(blank=True, max_length=20)),
        migrations.AddField(model_name="workerprofile", name="upi_id", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="workerprofile", name="payout_qr_token", field=models.CharField(blank=True, max_length=80, unique=True, null=True)),
    ]
