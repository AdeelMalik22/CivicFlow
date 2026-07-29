from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q, QuerySet
from django.views.generic import ListView

from .models import ServiceArea, Tenant, TenantMembership


class StaffRequiredMixin(UserPassesTestMixin):
    """Restrict platform-level organization views to staff users."""

    raise_exception = True

    def test_func(self) -> bool:
        return self.request.user.is_authenticated and self.request.user.is_staff


class TenantListView(StaffRequiredMixin, ListView):
    template_name = "tenants/tenant_list.html"
    context_object_name = "tenants"

    def get_queryset(self) -> QuerySet[Tenant]:
        return Tenant.objects.annotate(
            department_count=Count("departments", distinct=True),
            active_department_count=Count(
                "departments",
                filter=Q(departments__is_active=True),
                distinct=True,
            ),
            membership_count=Count("memberships", distinct=True),
            active_membership_count=Count(
                "memberships",
                filter=Q(memberships__status=TenantMembership.Status.ACTIVE),
                distinct=True,
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenants = context["tenants"]
        context["active_tenant_count"] = sum(
            tenant.status == Tenant.Status.ACTIVE for tenant in tenants
        )
        context["total_department_count"] = sum(tenant.department_count for tenant in tenants)
        return context


class ServiceAreaListView(StaffRequiredMixin, ListView):
    template_name = "tenants/service_area_list.html"
    context_object_name = "service_areas"

    def get_queryset(self) -> QuerySet[ServiceArea]:
        return ServiceArea.objects.select_related("tenant")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_areas = context["service_areas"]
        context["active_area_count"] = sum(area.is_active for area in service_areas)
        context["tenant_count"] = len({area.tenant_id for area in service_areas})
        return context


class TenantMembershipListView(StaffRequiredMixin, ListView):
    template_name = "tenants/membership_list.html"
    context_object_name = "memberships"

    def get_queryset(self) -> QuerySet[TenantMembership]:
        return TenantMembership.objects.select_related("tenant", "user", "invited_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        memberships = context["memberships"]
        context["active_membership_count"] = sum(
            membership.status == TenantMembership.Status.ACTIVE for membership in memberships
        )
        context["invited_membership_count"] = sum(
            membership.status == TenantMembership.Status.INVITED for membership in memberships
        )
        context["tenant_count"] = len({membership.tenant_id for membership in memberships})
        return context
