from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    AccessPermission,
    MembershipRole,
    RolePermission,
    SeparationOfDutiesPolicy,
    StaffInvitation,
    TenantRole,
    User,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("public_id", "last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal information", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("System", {"fields": ("public_id", "last_login", "date_joined")}),
    )


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0


@admin.register(TenantRole)
class TenantRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "code", "requires_mfa", "is_active")
    list_filter = ("tenant", "requires_mfa", "is_active")
    search_fields = ("name", "code", "tenant__name")
    inlines = (RolePermissionInline,)


@admin.register(AccessPermission)
class AccessPermissionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "default_scope", "is_sensitive")
    list_filter = ("default_scope", "is_sensitive")
    search_fields = ("name", "code")


@admin.register(MembershipRole)
class MembershipRoleAdmin(admin.ModelAdmin):
    list_display = ("membership", "role", "assigned_by", "assigned_at")
    list_filter = ("role__tenant", "role")
    autocomplete_fields = ("membership", "role", "assigned_by")


@admin.register(SeparationOfDutiesPolicy)
class SeparationOfDutiesPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "initiator_permission", "approver_permission", "is_active")
    list_filter = ("tenant", "is_active")


@admin.register(StaffInvitation)
class StaffInvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "membership", "invited_by", "sent_at", "accepted_at", "revoked_at")
    list_filter = ("sent_at", "accepted_at", "revoked_at")
    search_fields = ("email", "membership__tenant__name")
    readonly_fields = (
        "public_id",
        "membership",
        "email",
        "invited_by",
        "sent_at",
        "accepted_at",
        "revoked_at",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
