from django.contrib import admin

from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("category", "complainant", "status", "created_at", "resolved_by")
    list_filter = ("category", "status", "created_at")
    search_fields = ("complainant__email", "subject_user__email", "description")

