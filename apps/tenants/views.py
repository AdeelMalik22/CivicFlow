from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q, QuerySet
from django.views.generic import ListView

from .models import Tenant


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
            department_count=Count("departments"),
            active_department_count=Count(
                "departments",
                filter=Q(departments__is_active=True),
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
