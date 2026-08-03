from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Issue, IssueAttachment, IssueInternalNote, IssueStatusEvent


class IssueStatusEventInline(admin.TabularInline):
    model = IssueStatusEvent
    extra = 0
    readonly_fields = ("created_at",)


class IssueAttachmentInline(admin.TabularInline):
    model = IssueAttachment
    extra = 0
    readonly_fields = ("original_name", "checksum", "uploaded_at", "uploaded_by")


@admin.register(Issue)
class IssueAdmin(GISModelAdmin):
    list_display = ("reference", "category", "status", "tenant", "service_area", "created_at")
    list_filter = ("status", "category", "tenant", "service_area")
    search_fields = ("reference", "description", "reporter__email")
    readonly_fields = ("public_id", "reference", "created_at", "updated_at", "tracking_token_hash")
    autocomplete_fields = ("tenant", "service_area", "reporter", "assigned_to", "assigned_department")
    inlines = (IssueStatusEventInline, IssueAttachmentInline)


@admin.register(IssueStatusEvent)
class IssueStatusEventAdmin(admin.ModelAdmin):
    list_display = ("issue", "status", "actor", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("issue__reference", "public_message")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("issue", "actor")


@admin.register(IssueInternalNote)
class IssueInternalNoteAdmin(admin.ModelAdmin):
    list_display = ("issue", "author", "created_at")
    search_fields = ("issue__reference", "body", "author__email")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("issue", "author")


@admin.register(IssueAttachment)
class IssueAttachmentAdmin(admin.ModelAdmin):
    list_display = ("issue", "original_name", "uploaded_by", "uploaded_at")
    search_fields = ("issue__reference", "original_name", "checksum")
    readonly_fields = ("original_name", "checksum", "uploaded_at")
    autocomplete_fields = ("issue", "uploaded_by")
