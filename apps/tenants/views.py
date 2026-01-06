from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q, QuerySet
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import ServiceAreaForm, TenantForm, TenantMembershipForm
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


class EntityFormMixin(StaffRequiredMixin):
    template_name = "tenants/entity_form.html"
    success_message = "Saved successfully."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class TenantCreateView(EntityFormMixin, CreateView):
    model = Tenant
    form_class = TenantForm
    success_url = reverse_lazy("tenants:list")
    success_message = "Organization added."
    extra_context = {
        "eyebrow": "Platform administration",
        "form_title": "Add organization",
        "form_intro": "Create an isolated government organization in CivicFlow.",
        "submit_label": "Add organization",
        "cancel_url_name": "tenants:list",
        "form_variant": "organization",
    }


class TenantUpdateView(EntityFormMixin, UpdateView):
    model = Tenant
    form_class = TenantForm
    success_url = reverse_lazy("tenants:list")
    success_message = "Organization updated."
    extra_context = {
        **TenantCreateView.extra_context,
        "form_title": "Edit organization",
        "submit_label": "Save changes",
    }


class ServiceAreaCreateView(EntityFormMixin, CreateView):
    model = ServiceArea
    form_class = ServiceAreaForm
    success_url = reverse_lazy("tenants:service-area-list")
    success_message = "Service area added."
    extra_context = {
        "eyebrow": "Geographic configuration",
        "form_title": "Add service area",
        "form_intro": "Define the organization and geographic boundary used to route reports.",
        "submit_label": "Add service area",
        "cancel_url_name": "tenants:service-area-list",
        "form_variant": "service-area",
    }


class ServiceAreaUpdateView(EntityFormMixin, UpdateView):
    model = ServiceArea
    form_class = ServiceAreaForm
    success_url = reverse_lazy("tenants:service-area-list")
    success_message = "Service area updated."
    extra_context = {
        **ServiceAreaCreateView.extra_context,
        "form_title": "Edit service area",
        "submit_label": "Save changes",
    }


class TenantMembershipCreateView(EntityFormMixin, CreateView):
    model = TenantMembership
    form_class = TenantMembershipForm
    success_url = reverse_lazy("tenants:membership-list")
    success_message = "Membership added."
    extra_context = {
        "eyebrow": "Identity administration",
        "form_title": "Add membership",
        "form_intro": "Connect an existing CivicFlow account to an organization.",
        "submit_label": "Add membership",
        "cancel_url_name": "tenants:membership-list",
        "form_variant": "membership",
    }

    def form_valid(self, form):
        if form.instance._state.adding:
            form.instance.invited_by = self.request.user
        return super().form_valid(form)


class TenantMembershipUpdateView(EntityFormMixin, UpdateView):
    model = TenantMembership
    form_class = TenantMembershipForm
    success_url = reverse_lazy("tenants:membership-list")
    success_message = "Membership updated."
    extra_context = {
        **TenantMembershipCreateView.extra_context,
        "form_title": "Edit membership",
        "submit_label": "Save changes",
    }
