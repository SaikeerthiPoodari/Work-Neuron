from django.contrib import admin

from .models import Skill, WorkerSkill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_active", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("name", "category")


@admin.register(WorkerSkill)
class WorkerSkillAdmin(admin.ModelAdmin):
    list_display = ("worker", "skill", "proficiency", "years_experience", "updated_at")
    list_filter = ("proficiency", "skill")
    search_fields = ("worker__email", "skill__name")

