from django.contrib import admin

from .models import ContractorApplication


@admin.register(ContractorApplication)
class ContractorApplicationAdmin(admin.ModelAdmin):
    list_display = ("company_name", "registration_number", "applicant", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("company_name", "registration_number", "applicant__email")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("applicant", "reviewed_by")
