from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q, QuerySet
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import SeparationOfDutiesPolicyForm, TenantRoleForm
from .models import SeparationOfDutiesPolicy, TenantRole


class PlatformStaffRequiredMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self) -> bool:
        return self.request.user.is_authenticated and self.request.user.is_staff


class TenantRoleListView(PlatformStaffRequiredMixin, ListView):
    model = TenantRole
    template_name = "accounts/role_list.html"
    context_object_name = "roles"

    def get_queryset(self) -> QuerySet[TenantRole]:
        return TenantRole.objects.select_related("tenant").annotate(
            member_count=Count("membership_assignments", distinct=True),
            permission_count=Count("grants", distinct=True),
            sensitive_permission_count=Count(
                "grants",
                filter=Q(grants__permission__is_sensitive=True),
                distinct=True,
            ),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["separation_policies"] = SeparationOfDutiesPolicy.objects.select_related(
            "tenant",
            "initiator_permission",
            "approver_permission",
        )
        return context


class RoleFormMixin(PlatformStaffRequiredMixin):
    model = TenantRole
    form_class = TenantRoleForm
    template_name = "accounts/role_form.html"
    success_url = reverse_lazy("accounts:role-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class TenantRoleCreateView(RoleFormMixin, CreateView):
    success_message = "Role created."


class TenantRoleUpdateView(RoleFormMixin, UpdateView):
    success_message = "Role updated."


class SeparationPolicyFormMixin(PlatformStaffRequiredMixin):
    model = SeparationOfDutiesPolicy
    form_class = SeparationOfDutiesPolicyForm
    template_name = "accounts/separation_policy_form.html"
    success_url = reverse_lazy("accounts:role-list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response


class SeparationPolicyCreateView(SeparationPolicyFormMixin, CreateView):
    success_message = "Separation-of-duties policy created."


class SeparationPolicyUpdateView(SeparationPolicyFormMixin, UpdateView):
    success_message = "Separation-of-duties policy updated."
