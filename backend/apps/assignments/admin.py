from django.contrib import admin

from .models import Assignment, AssignmentLevel


class AssignmentLevelInline(admin.TabularInline):
    model = AssignmentLevel
    extra = 0
    ordering = ("order",)
    readonly_fields = ("status", "submission", "feedback", "submitted_at", "reviewed_at")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("task", "worker", "progress", "created_at", "submitted_at", "completed_at")
    search_fields = ("task__title", "worker__email")
    inlines = (AssignmentLevelInline,)
