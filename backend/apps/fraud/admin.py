from django.contrib import admin

from .models import FraudAlert


@admin.register(FraudAlert)
class FraudAlertAdmin(admin.ModelAdmin):
    list_display = ("alert_type", "user", "score", "status", "created_at")
    list_filter = ("alert_type", "status", "created_at")
    search_fields = ("user__email", "resolution_notes")

