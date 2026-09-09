from django.contrib import admin

from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("task", "worker", "progress", "created_at", "submitted_at", "completed_at")
    search_fields = ("task__title", "worker__email")

