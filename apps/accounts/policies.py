from dataclasses import dataclass

from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant, TenantMembership

from .models import AccessPermission, RolePermission, SeparationOfDutiesPolicy

User = get_user_model()


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    scope: str | None = None
    reason: str = ""


def permission_for(
    user: User,
    tenant: Tenant,
    permission_code: str,
) -> PermissionDecision:
    """Resolve a user's strongest active grant inside one tenant."""
    if not user.is_authenticated or not user.is_active:
        return PermissionDecision(False, reason="An active account is required.")

    if user.is_superuser:
        return PermissionDecision(True, AccessPermission.Scope.TENANT)

    membership = (
        TenantMembership.objects.active()
        .filter(user=user, tenant=tenant)
        .first()
    )
    if membership is None:
        return PermissionDecision(False, reason="No active membership in this organization.")

    scope_order = {
        AccessPermission.Scope.OWN: 1,
        AccessPermission.Scope.ASSIGNED: 2,
        AccessPermission.Scope.TENANT: 3,
    }
    scopes = RolePermission.objects.filter(
        role__membership_assignments__membership=membership,
        role__is_active=True,
        permission__code=permission_code,
    ).values_list("scope", flat=True)
    strongest = max(scopes, key=scope_order.get, default=None)
    if strongest is None:
        return PermissionDecision(False, reason="The required permission is not assigned.")
    return PermissionDecision(True, strongest)


def can(
    user: User,
    tenant: Tenant,
    permission_code: str,
) -> bool:
    return permission_for(user, tenant, permission_code).allowed


def separation_allows(
    *,
    actor: User,
    initiator: User | None,
    tenant: Tenant,
    approval_permission: str,
) -> PermissionDecision:
    """Apply configured self-approval restrictions after the normal grant check."""
    grant = permission_for(actor, tenant, approval_permission)
    if not grant.allowed:
        return grant
    if initiator is None or actor.pk != initiator.pk:
        return grant

    restricted = SeparationOfDutiesPolicy.objects.filter(
        tenant=tenant,
        approver_permission__code=approval_permission,
        is_active=True,
    ).exists()
    if restricted:
        return PermissionDecision(
            False,
            reason="Separation-of-duties policy prevents self-approval.",
        )
    return grant
