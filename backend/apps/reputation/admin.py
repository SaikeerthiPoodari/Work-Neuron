from django.contrib import admin

from .models import ReputationScore


@admin.register(ReputationScore)
class ReputationScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "average_rating", "completion_rate", "score", "updated_at")
    search_fields = ("user__email",)

