import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from apps.accounts.models import (
    AccessPermission,
    MembershipRole,
    RolePermission,
    SeparationOfDutiesPolicy,
    TenantRole,
)
from apps.accounts.policies import permission_for, separation_allows
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


@pytest.mark.django_db
def test_role_policy_workspace_requires_platform_staff(client: Client):
    user = User.objects.create_user(email="member@example.com")
    client.force_login(user)

    assert client.get(reverse("accounts:role-list")).status_code == 403


@pytest.mark.django_db
def test_platform_staff_can_create_tenant_role(client: Client):
    staff = User.objects.create_user(email="staff@example.com", is_staff=True)
    tenant = Tenant.objects.create(name="City", slug="city")
    permission, _ = AccessPermission.objects.update_or_create(
        code="issue.triage",
        defaults={"name": "Triage issues"},
    )
    client.force_login(staff)

    response = client.post(
        reverse("accounts:role-add"),
        {
            "tenant": tenant.pk,
            "name": "Government Officer",
            "code": "OFFICER",
            "description": "Reviews incoming issues.",
            "requires_mfa": "on",
            "is_active": "on",
            "permissions": [permission.pk],
        },
    )

    role = TenantRole.objects.get()
    assert response.status_code == 302
    assert role.code == "officer"
    assert role.permissions.get() == permission


@pytest.mark.django_db
def test_permission_is_denied_without_active_membership():
    user = User.objects.create_user(email="officer@example.com")
    tenant = Tenant.objects.create(name="City", slug="city", status=Tenant.Status.ACTIVE)

    decision = permission_for(user, tenant, "issue.triage")

    assert not decision.allowed


@pytest.mark.django_db
def test_role_grants_tenant_scoped_permission():
    user = User.objects.create_user(email="officer@example.com")
    tenant = Tenant.objects.create(name="City", slug="city", status=Tenant.Status.ACTIVE)
    membership = TenantMembership.objects.create(
        user=user,
        tenant=tenant,
        status=TenantMembership.Status.ACTIVE,
    )
    permission, _ = AccessPermission.objects.update_or_create(
        code="issue.triage",
        defaults={
            "name": "Triage issues",
            "default_scope": AccessPermission.Scope.ASSIGNED,
        },
    )
    role = TenantRole.objects.create(tenant=tenant, name="Officer", code="OFFICER")
    RolePermission.objects.create(
        role=role,
        permission=permission,
        scope=AccessPermission.Scope.ASSIGNED,
    )
    MembershipRole.objects.create(membership=membership, role=role)

    decision = permission_for(user, tenant, "issue.triage")

    assert decision.allowed
    assert decision.scope == AccessPermission.Scope.ASSIGNED


@pytest.mark.django_db
def test_membership_cannot_receive_role_from_another_tenant():
    first = Tenant.objects.create(name="First", slug="first")
    second = Tenant.objects.create(name="Second", slug="second")
    user = User.objects.create_user(email="officer@example.com")
    membership = TenantMembership.objects.create(tenant=first, user=user)
    role = TenantRole.objects.create(tenant=second, name="Officer", code="officer")

    with pytest.raises(ValidationError):
        MembershipRole.objects.create(membership=membership, role=role)


@pytest.mark.django_db
def test_separation_policy_prevents_self_approval():
    user = User.objects.create_user(email="finance@example.com")
    tenant = Tenant.objects.create(name="City", slug="city", status=Tenant.Status.ACTIVE)
    membership = TenantMembership.objects.create(
        user=user,
        tenant=tenant,
        status=TenantMembership.Status.ACTIVE,
    )
    submit, _ = AccessPermission.objects.update_or_create(
        code="payment.request",
        defaults={"name": "Request payment"},
    )
    approve, _ = AccessPermission.objects.update_or_create(
        code="payment.approve",
        defaults={"name": "Approve payment"},
    )
    role = TenantRole.objects.create(tenant=tenant, name="Finance", code="finance")
    RolePermission.objects.create(
        role=role,
        permission=approve,
        scope=AccessPermission.Scope.ASSIGNED,
    )
    MembershipRole.objects.create(membership=membership, role=role)
    SeparationOfDutiesPolicy.objects.create(
        tenant=tenant,
        name="Payment maker-checker",
        initiator_permission=submit,
        approver_permission=approve,
    )

    decision = separation_allows(
        actor=user,
        initiator=user,
        tenant=tenant,
        approval_permission="payment.approve",
    )

    assert not decision.allowed
    assert "self-approval" in decision.reason
