from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Tenant, TenantMembership

ACTIVE_TENANT_SESSION_KEY = "active_tenant_public_id"


def active_memberships_for(request: HttpRequest) -> QuerySet[TenantMembership]:
    if not request.user.is_authenticated:
        return TenantMembership.objects.none()
    return TenantMembership.objects.active().filter(user=request.user).select_related("tenant")


def require_active_tenant(request: HttpRequest) -> Tenant:
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        raise PermissionDenied("Select an active organization to continue.")
    return tenant


def activate_tenant(request: HttpRequest, tenant: Tenant) -> TenantMembership:
    """Persist a tenant only after verifying an active membership."""
    membership = active_memberships_for(request).filter(tenant=tenant).first()
    if membership is None:
        raise PermissionDenied("You do not have an active membership in this organization.")
    request.session[ACTIVE_TENANT_SESSION_KEY] = str(tenant.public_id)
    request.tenant = tenant
    request.tenant_membership = membership
    return membership


def clear_active_tenant(request: HttpRequest) -> None:
    request.session.pop(ACTIVE_TENANT_SESSION_KEY, None)
    request.tenant = None
    request.tenant_membership = None
