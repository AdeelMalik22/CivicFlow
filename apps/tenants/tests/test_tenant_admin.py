import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.accounts.models import (
    AccessPermission,
    MembershipRole,
    RolePermission,
    TenantRole,
)
from apps.tenants.models import Department, Tenant, TenantMembership

User = get_user_model()


def active_tenant(name: str, slug: str) -> Tenant:
    return Tenant.objects.create(name=name, slug=slug, status=Tenant.Status.ACTIVE)


def tenant_administrator(*, tenant: Tenant, permission_code: str):
    user = User.objects.create_user(email=f"{permission_code}@example.com")
    membership = TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        status=TenantMembership.Status.ACTIVE,
    )
    permission, _ = AccessPermission.objects.update_or_create(
        code=permission_code,
        defaults={"name": permission_code.replace(".", " ").title()},
    )
    role = TenantRole.objects.create(
        tenant=tenant,
        name=f"{permission.name} administrator",
        code=f"{permission_code}-admin",
    )
    RolePermission.objects.create(
        role=role,
        permission=permission,
        scope=AccessPermission.Scope.TENANT,
    )
    MembershipRole.objects.create(membership=membership, role=role)
    return user


@pytest.mark.django_db
def test_member_without_admin_capability_is_denied(client: Client):
    tenant = active_tenant("City", "city")
    user = User.objects.create_user(email="officer@example.com")
    TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        status=TenantMembership.Status.ACTIVE,
    )
    client.force_login(user)

    response = client.get(reverse("tenant-admin:dashboard"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_dashboard_contains_only_active_tenant_records(client: Client):
    first = active_tenant("First City", "first")
    second = active_tenant("Second City", "second")
    Department.objects.create(tenant=first, name="First Roads", code="ROADS")
    Department.objects.create(tenant=second, name="Secret Roads", code="SECRET")
    user = tenant_administrator(tenant=first, permission_code="configuration.manage")
    client.force_login(user)

    response = client.get(reverse("tenant-admin:dashboard"))

    assert response.status_code == 200
    assert b"First Roads" in response.content
    assert b"Secret Roads" not in response.content


@pytest.mark.django_db
def test_department_create_ignores_client_tenant_and_uses_request_tenant(client: Client):
    allowed = active_tenant("Allowed", "allowed")
    other = active_tenant("Other", "other")
    user = tenant_administrator(tenant=allowed, permission_code="configuration.manage")
    client.force_login(user)

    response = client.post(
        reverse("tenant-admin:department-add"),
        {
            "tenant": other.pk,
            "name": "Roads",
            "code": "ROADS",
            "description": "",
            "is_active": "on",
        },
    )

    department = Department.objects.get()
    assert response.status_code == 302
    assert department.tenant == allowed


@pytest.mark.django_db
def test_cross_tenant_department_edit_returns_not_found(client: Client):
    allowed = active_tenant("Allowed", "allowed")
    other = active_tenant("Other", "other")
    foreign_department = Department.objects.create(
        tenant=other,
        name="Other Roads",
        code="ROADS",
    )
    user = tenant_administrator(tenant=allowed, permission_code="configuration.manage")
    client.force_login(user)

    response = client.get(
        reverse("tenant-admin:department-edit", args=(foreign_department.pk,))
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_user_manager_can_invite_only_into_active_tenant(client: Client):
    allowed = active_tenant("Allowed", "allowed")
    other = active_tenant("Other", "other")
    user = tenant_administrator(tenant=allowed, permission_code="users.manage")
    client.force_login(user)

    response = client.post(
        reverse("tenant-admin:membership-add"),
        {
            "tenant": other.pk,
            "email": "new-member@example.com",
            "first_name": "New",
            "last_name": "Member",
        },
    )

    membership = TenantMembership.objects.exclude(user=user).get()
    assert response.status_code == 302
    assert membership.tenant == allowed
    assert membership.status == TenantMembership.Status.INVITED
