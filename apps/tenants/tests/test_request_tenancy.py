from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import Client
from django.urls import reverse

from apps.tenants.models import Department, ServiceArea, Tenant, TenantMembership
from apps.tenants.request import ACTIVE_TENANT_SESSION_KEY

User = get_user_model()


def active_tenant(name: str, slug: str) -> Tenant:
    return Tenant.objects.create(name=name, slug=slug, status=Tenant.Status.ACTIVE)


@pytest.mark.django_db
def test_single_active_membership_is_resolved_automatically(client: Client):
    user = User.objects.create_user(email="officer@example.com")
    tenant = active_tenant("City Services", "city")
    TenantMembership.objects.create(
        user=user,
        tenant=tenant,
        status=TenantMembership.Status.ACTIVE,
    )
    client.force_login(user)

    response = client.get(reverse("workspace"))

    assert response.wsgi_request.tenant == tenant
    assert response.wsgi_request.tenant_membership.user == user
    assert client.session[ACTIVE_TENANT_SESSION_KEY] == str(tenant.public_id)


@pytest.mark.django_db
def test_multiple_memberships_require_an_explicit_selection(client: Client):
    user = User.objects.create_user(email="officer@example.com")
    first = active_tenant("First", "first")
    second = active_tenant("Second", "second")
    for tenant in (first, second):
        TenantMembership.objects.create(
            user=user,
            tenant=tenant,
            status=TenantMembership.Status.ACTIVE,
        )
    client.force_login(user)

    response = client.get(reverse("workspace"))

    assert response.wsgi_request.tenant is None
    assert ACTIVE_TENANT_SESSION_KEY not in client.session


@pytest.mark.django_db
def test_user_can_switch_only_to_an_active_membership(client: Client):
    user = User.objects.create_user(email="officer@example.com")
    allowed = active_tenant("Allowed", "allowed")
    forbidden = active_tenant("Forbidden", "forbidden")
    TenantMembership.objects.create(
        user=user,
        tenant=allowed,
        status=TenantMembership.Status.ACTIVE,
    )
    client.force_login(user)

    denied = client.post(reverse("tenants:select", args=(forbidden.public_id,)))
    selected = client.post(reverse("tenants:select", args=(allowed.public_id,)))

    assert denied.status_code == 403
    assert selected.status_code == 302
    assert client.session[ACTIVE_TENANT_SESSION_KEY] == str(allowed.public_id)


@pytest.mark.django_db
def test_suspended_membership_clears_previous_tenant_selection(client: Client):
    user = User.objects.create_user(email="officer@example.com")
    tenant = active_tenant("City", "city")
    membership = TenantMembership.objects.create(
        user=user,
        tenant=tenant,
        status=TenantMembership.Status.ACTIVE,
    )
    client.force_login(user)
    client.post(reverse("tenants:select", args=(tenant.public_id,)))
    membership.suspend()

    response = client.get(reverse("workspace"))

    assert response.wsgi_request.tenant is None
    assert ACTIVE_TENANT_SESSION_KEY not in client.session


@pytest.mark.django_db
def test_tenant_scoped_queryset_never_returns_another_tenants_records():
    first = active_tenant("First", "first")
    second = active_tenant("Second", "second")
    expected = Department.objects.create(tenant=first, name="Roads", code="ROADS")
    Department.objects.create(tenant=second, name="Finance", code="FINANCE")

    request = SimpleNamespace(tenant=first)

    assert list(Department.objects.for_request(request)) == [expected]


@pytest.mark.django_db
def test_tenant_scoped_queryset_denies_request_without_active_tenant():
    request = SimpleNamespace(tenant=None)

    with pytest.raises(PermissionDenied):
        ServiceArea.objects.for_request(request)
