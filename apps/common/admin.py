from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("reference", "name", "tenant", "status", "target_date", "budget", "created_at")
    list_filter = ("status", "tenant")
    search_fields = ("reference", "name", "tenant__name")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("tenant", "created_by")
