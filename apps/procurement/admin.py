from django.contrib import admin

from .models import Award, Bid, ProcurementAuditEvent, Tender


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ("reference", "title", "category", "published", "deadline", "created_by")
    list_filter = ("published", "category", "procurement_method")
    search_fields = ("reference", "title", "description")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("department", "service_area", "created_by")


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("tender", "contractor", "amount", "submitted_at")
    list_filter = ("submitted_at",)
    search_fields = ("tender__reference", "contractor__email")
    readonly_fields = ("submitted_at",)
    autocomplete_fields = ("tender", "contractor")


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ("tender", "winning_bid", "awarded_by", "awarded_at")
    search_fields = ("tender__reference", "winning_bid__contractor__email")
    readonly_fields = ("awarded_at",)
    autocomplete_fields = ("tender", "winning_bid", "awarded_by")


@admin.register(ProcurementAuditEvent)
class ProcurementAuditEventAdmin(admin.ModelAdmin):
    list_display = ("tender", "action", "actor", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("tender__reference", "action", "note")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("tender", "actor")
