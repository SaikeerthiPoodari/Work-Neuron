from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("task", "worker", "status", "proposed_budget", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("task__title", "worker__email")

