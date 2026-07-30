from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db import models
from django.http import HttpRequest


class TenantScopedQuerySet(models.QuerySet):
    """Reusable deny-by-default helpers for tenant-owned records."""

    tenant_lookup = "tenant"

    def for_tenant(self, tenant):
        return self.filter(**{self.tenant_lookup: tenant})

    def for_request(self, request: HttpRequest):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            raise PermissionDenied("Select an active organization to continue.")
        return self.for_tenant(tenant)


class TenantScopedQuerysetMixin:
    """Scope class-based-view querysets before object lookup or authorization."""

    tenant_lookup = "tenant"

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.tenant_lookup:
            raise ImproperlyConfigured("tenant_lookup must be configured.")
        tenant = getattr(self.request, "tenant", None)
        if tenant is None:
            raise PermissionDenied("Select an active organization to continue.")
        return queryset.filter(**{self.tenant_lookup: tenant})
