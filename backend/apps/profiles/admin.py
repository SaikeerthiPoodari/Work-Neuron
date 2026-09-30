from django.contrib import admin

from .models import ClientProfile, WorkerProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization_name", "employer_type", "location", "updated_at")
    search_fields = ("user__email", "organization_name", "location")


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "headline", "experience_years", "availability", "preferred_job_type", "location")
    search_fields = ("user__email", "headline", "location")
