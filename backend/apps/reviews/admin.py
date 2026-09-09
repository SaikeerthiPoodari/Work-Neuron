from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("assignment", "reviewer", "reviewed_user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("reviewer__email", "reviewed_user__email", "review")

