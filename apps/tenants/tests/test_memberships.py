import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


@pytest.mark.django_db
def test_membership_defaults_to_invited_with_stable_reference():
    tenant = Tenant.objects.create(name="Metropolitan Services", slug="metro")
    user = User.objects.create_user(email="officer@example.com")

    membership = TenantMembership.objects.create(tenant=tenant, user=user)

    assert membership.status == TenantMembership.Status.INVITED
    assert membership.public_id is not None
    assert membership.invited_at is not None
    assert membership.activated_at is None
    assert membership.suspended_at is None


@pytest.mark.django_db
def test_membership_activation_and_suspension_track_lifecycle_dates():
    tenant = Tenant.objects.create(
        name="Metropolitan Services",
        slug="metro",
        status=Tenant.Status.ACTIVE,
    )
    user = User.objects.create_user(email="officer@example.com")
    membership = TenantMembership.objects.create(tenant=tenant, user=user)

    membership.activate()
    assert membership.status == TenantMembership.Status.ACTIVE
    assert membership.activated_at is not None
    assert membership.suspended_at is None

    membership.suspend()
    assert membership.status == TenantMembership.Status.SUSPENDED
    assert membership.suspended_at is not None

    membership.activate()
    assert membership.status == TenantMembership.Status.ACTIVE
    assert membership.suspended_at is None


@pytest.mark.django_db
def test_user_can_have_only_one_membership_per_tenant():
    tenant = Tenant.objects.create(name="Metropolitan Services", slug="metro")
    user = User.objects.create_user(email="officer@example.com")
    TenantMembership.objects.create(tenant=tenant, user=user)

    with pytest.raises(IntegrityError), transaction.atomic():
        TenantMembership.objects.create(tenant=tenant, user=user)


@pytest.mark.django_db
def test_same_user_can_belong_to_multiple_tenants():
    first_tenant = Tenant.objects.create(name="First", slug="first")
    second_tenant = Tenant.objects.create(name="Second", slug="second")
    user = User.objects.create_user(email="auditor@example.com")

    TenantMembership.objects.create(tenant=first_tenant, user=user)
    TenantMembership.objects.create(tenant=second_tenant, user=user)

    assert TenantMembership.objects.for_user(user).count() == 2


@pytest.mark.django_db
def test_active_memberships_require_active_tenant_and_user():
    active_tenant = Tenant.objects.create(
        name="Active",
        slug="active",
        status=Tenant.Status.ACTIVE,
    )
    suspended_tenant = Tenant.objects.create(
        name="Suspended",
        slug="suspended",
        status=Tenant.Status.SUSPENDED,
    )
    active_user = User.objects.create_user(email="active@example.com")
    inactive_user = User.objects.create_user(
        email="inactive@example.com",
        is_active=False,
    )
    expected = TenantMembership.objects.create(
        tenant=active_tenant,
        user=active_user,
        status=TenantMembership.Status.ACTIVE,
    )
    TenantMembership.objects.create(
        tenant=suspended_tenant,
        user=active_user,
        status=TenantMembership.Status.ACTIVE,
    )
    TenantMembership.objects.create(
        tenant=active_tenant,
        user=inactive_user,
        status=TenantMembership.Status.ACTIVE,
    )

    assert list(TenantMembership.objects.active()) == [expected]


@pytest.mark.django_db
def test_membership_protects_tenant_and_user_from_deletion():
    tenant = Tenant.objects.create(name="Protected", slug="protected")
    user = User.objects.create_user(email="protected@example.com")
    TenantMembership.objects.create(tenant=tenant, user=user)

    with pytest.raises(ProtectedError):
        tenant.delete()
    with pytest.raises(ProtectedError):
        user.delete()
