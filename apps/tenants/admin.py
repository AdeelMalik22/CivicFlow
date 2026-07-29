from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Department, ServiceArea, Tenant


class DepartmentInline(admin.TabularInline):
    model = Department
    fields = ("name", "code", "is_active")
    extra = 0
    show_change_link = True


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "timezone", "department_count")
    list_filter = ("status", "timezone", "default_language")
    search_fields = ("name", "slug", "contact_email")
    readonly_fields = ("public_id", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (DepartmentInline,)

    @admin.display(description="Departments")
    def department_count(self, tenant: Tenant) -> int:
        return tenant.departments.count()


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "tenant", "is_active", "updated_at")
    list_filter = ("is_active", "tenant")
    search_fields = ("name", "code", "tenant__name")
    readonly_fields = ("public_id", "created_at", "updated_at")
    autocomplete_fields = ("tenant",)


@admin.register(ServiceArea)
class ServiceAreaAdmin(GISModelAdmin):
    list_display = ("name", "code", "tenant", "is_active", "updated_at")
    list_filter = ("is_active", "tenant")
    search_fields = ("name", "code", "tenant__name")
    readonly_fields = ("public_id", "created_at", "updated_at")
    autocomplete_fields = ("tenant",)
