from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView

from apps.accounts.forms import TenantRoleForm
from apps.accounts.models import TenantRole
from apps.accounts.policies import can
from apps.accounts.services import (
    InvitationError,
    activate_membership,
    issue_staff_invitation,
    suspend_membership,
)

from .forms import (
    DepartmentForm,
    ServiceAreaForm,
    TenantMembershipForm,
    TenantSettingsForm,
)
from .models import Department, ServiceArea, TenantMembership


class TenantAdministrationAccessMixin(UserPassesTestMixin):
    raise_exception = True
    required_permissions: tuple[str, ...] = ()

    def test_func(self) -> bool:
        tenant = getattr(self.request, "tenant", None)
        if tenant is None or not self.request.user.is_authenticated:
            return False
        return any(can(self.request.user, tenant, code) for code in self.required_permissions)


class TenantAdministrationDashboardView(TenantAdministrationAccessMixin, TemplateView):
    template_name = "tenants/admin/dashboard.html"
    required_permissions = ("configuration.manage", "users.manage")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        memberships = TenantMembership.objects.for_tenant(tenant).select_related("user")
        roles = TenantRole.objects.for_tenant(tenant).annotate(
            member_count=Count("membership_assignments", distinct=True),
            permission_count=Count("grants", distinct=True),
        )
        context.update(
            {
                "departments": Department.objects.for_tenant(tenant),
                "service_areas": ServiceArea.objects.for_tenant(tenant),
                "memberships": memberships.prefetch_related(
                    "role_assignments__role"
                ),
                "roles": roles,
                "active_member_count": memberships.filter(
                    status=TenantMembership.Status.ACTIVE
                ).count(),
                "can_manage_configuration": can(
                    self.request.user, tenant, "configuration.manage"
                ),
                "can_manage_users": can(self.request.user, tenant, "users.manage"),
            }
        )
        return context


class ConfigurationPermissionMixin(TenantAdministrationAccessMixin):
    required_permissions = ("configuration.manage",)


class UserManagementPermissionMixin(TenantAdministrationAccessMixin):
    required_permissions = ("users.manage",)


class TenantSettingsUpdateView(ConfigurationPermissionMixin, UpdateView):
    form_class = TenantSettingsForm
    template_name = "tenants/admin/settings_form.html"
    success_url = reverse_lazy("tenant-admin:dashboard")

    def get_object(self, queryset=None):
        return self.request.tenant

    def form_valid(self, form):
        messages.success(self.request, "Organization settings updated.")
        return super().form_valid(form)


class DepartmentFormMixin(ConfigurationPermissionMixin):
    model = Department
    form_class = DepartmentForm
    template_name = "tenants/admin/department_form.html"
    success_url = reverse_lazy("tenant-admin:dashboard")

    def get_queryset(self):
        return Department.objects.for_request(self.request)

    def form_valid(self, form):
        form.instance.tenant = self.request.tenant
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class DepartmentCreateView(DepartmentFormMixin, CreateView):
    success_message = "Department created."


class DepartmentUpdateView(DepartmentFormMixin, UpdateView):
    success_message = "Department updated."


class TenantBoundFormMixin:
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "tenant" in form.fields:
            form.fields["tenant"].initial = self.request.tenant
            form.fields["tenant"].disabled = True
            form.fields["tenant"].queryset = form.fields["tenant"].queryset.filter(
                pk=self.request.tenant.pk
            )
        if "roles" in form.fields:
            form.fields["roles"].queryset = TenantRole.objects.for_tenant(
                self.request.tenant
            ).filter(is_active=True)
        if "department" in form.fields:
            form.fields["department"].queryset = Department.objects.for_tenant(
                self.request.tenant
            ).filter(is_active=True)
        return form


class TenantServiceAreaFormMixin(
    TenantBoundFormMixin,
    ConfigurationPermissionMixin,
):
    model = ServiceArea
    form_class = ServiceAreaForm
    template_name = "tenants/service_area_form.html"
    success_url = reverse_lazy("tenant-admin:dashboard")
    extra_context = {
        "eyebrow": "Tenant administration",
        "form_intro": "Configure a report-routing boundary for the active organization.",
        "cancel_url_name": "tenant-admin:dashboard",
        "form_variant": "service-area",
    }

    def get_queryset(self):
        return ServiceArea.objects.for_request(self.request)

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class TenantServiceAreaCreateView(TenantServiceAreaFormMixin, CreateView):
    success_message = "Service area created."
    extra_context = {
        **TenantServiceAreaFormMixin.extra_context,
        "form_title": "Add service area",
        "submit_label": "Add service area",
    }


class TenantServiceAreaUpdateView(TenantServiceAreaFormMixin, UpdateView):
    success_message = "Service area updated."
    extra_context = {
        **TenantServiceAreaFormMixin.extra_context,
        "form_title": "Edit service area",
        "submit_label": "Save changes",
    }


class TenantMembershipFormMixin(TenantBoundFormMixin, UserManagementPermissionMixin):
    model = TenantMembership
    form_class = TenantMembershipForm
    template_name = "tenants/entity_form.html"
    success_url = reverse_lazy("tenant-admin:dashboard")
    extra_context = {
        "eyebrow": "Tenant administration",
        "form_intro": "Invite an account and assign roles in the active organization.",
        "cancel_url_name": "tenant-admin:dashboard",
        "form_variant": "membership",
    }

    def get_queryset(self):
        return TenantMembership.objects.for_request(self.request)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["inviter"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.assigned_by = self.request.user
        was_adding = form.instance._state.adding
        if was_adding:
            form.instance.invited_by = self.request.user
        response = super().form_valid(form)
        if was_adding and self.object.status == TenantMembership.Status.INVITED:
            issue_staff_invitation(
                self.object,
                invited_by=self.request.user,
                build_absolute_uri=self.request.build_absolute_uri,
            )
        messages.success(self.request, self.success_message)
        return response


class TenantMembershipCreateView(TenantMembershipFormMixin, CreateView):
    success_message = "Staff invitation created."
    extra_context = {
        **TenantMembershipFormMixin.extra_context,
        "form_title": "Invite staff member",
        "submit_label": "Send invitation",
    }


class TenantMembershipUpdateView(TenantMembershipFormMixin, UpdateView):
    success_message = "Membership roles updated."
    extra_context = {
        **TenantMembershipFormMixin.extra_context,
        "form_title": "Edit member access",
        "submit_label": "Save access",
    }


class TenantRoleFormMixin(TenantBoundFormMixin, UserManagementPermissionMixin):
    model = TenantRole
    form_class = TenantRoleForm
    template_name = "accounts/role_form.html"
    success_url = reverse_lazy("tenant-admin:dashboard")
    extra_context = {"cancel_url_name": "tenant-admin:dashboard"}

    def get_queryset(self):
        return TenantRole.objects.for_request(self.request)

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


class TenantRoleCreateView(TenantRoleFormMixin, CreateView):
    success_message = "Role created."


class TenantRoleUpdateView(TenantRoleFormMixin, UpdateView):
    success_message = "Role updated."


class TenantMembershipLifecycleView(UserManagementPermissionMixin, View):
    action = ""

    def post(self, request, pk):
        membership = get_object_or_404(
            TenantMembership.objects.for_request(request).select_related("user"),
            pk=pk,
        )
        if self.action == "suspend":
            suspend_membership(membership)
            messages.success(request, f"{membership.user} was suspended.")
        elif self.action == "activate":
            activate_membership(membership)
            messages.success(request, f"{membership.user} was activated.")
        elif self.action == "resend":
            try:
                issue_staff_invitation(
                    membership,
                    invited_by=request.user,
                    build_absolute_uri=request.build_absolute_uri,
                )
            except InvitationError as error:
                messages.error(request, error.message)
            else:
                messages.success(request, f"Invitation resent to {membership.user.email}.")
        return HttpResponseRedirect(reverse_lazy("tenant-admin:dashboard"))


class TenantMembershipSuspendView(TenantMembershipLifecycleView):
    action = "suspend"


class TenantMembershipActivateView(TenantMembershipLifecycleView):
    action = "activate"


class TenantMembershipResendView(TenantMembershipLifecycleView):
    action = "resend"
