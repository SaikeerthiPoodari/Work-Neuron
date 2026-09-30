from django.contrib import admin

from .models import EmployerVerification, VerificationDocument


@admin.register(EmployerVerification)
class EmployerVerificationAdmin(admin.ModelAdmin):
    list_display = ("legal_name", "employer", "employer_type", "status", "submitted_at", "reviewed_at")
    list_filter = ("status", "employer_type")
    search_fields = ("legal_name", "business_name", "employer__email", "registration_number")


@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ("label", "verification", "uploaded_at")
    search_fields = ("label", "verification__legal_name", "verification__employer__email")
