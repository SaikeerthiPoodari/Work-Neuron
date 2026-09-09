from django.contrib import admin

from .models import Task, TaskSkill


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "budget", "deadline", "status", "created_at")
    list_filter = ("status", "deadline")
    search_fields = ("title", "description", "owner__email", "location")


@admin.register(TaskSkill)
class TaskSkillAdmin(admin.ModelAdmin):
    list_display = ("task", "skill")
    search_fields = ("task__title", "skill__name")

