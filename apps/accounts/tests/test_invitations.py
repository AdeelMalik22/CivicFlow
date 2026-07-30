import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from apps.accounts.services import invitation_path, issue_staff_invitation
from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


def invited_membership(*, existing_account: bool = False):
    tenant = Tenant.objects.create(
        name="City Services",
        slug="city-services",
        status=Tenant.Status.ACTIVE,
    )
    user = User.objects.create_user(
        email="officer@example.com",
        password="existing-safe-password" if existing_account else None,
    )
    if not existing_account:
        user.set_unusable_password()
        user.save(update_fields=("password",))
    membership = TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        status=TenantMembership.Status.INVITED,
    )
    return membership


@pytest.mark.django_db
def test_issuing_invitation_records_attempt_and_sends_after_commit(
    django_capture_on_commit_callbacks,
):
    membership = invited_membership()
    inviter = User.objects.create_user(email="admin@example.com", is_staff=True)

    with django_capture_on_commit_callbacks(execute=True):
        invitation = issue_staff_invitation(
            membership,
            invited_by=inviter,
            build_absolute_uri=lambda path: f"https://civicflow.test{path}",
        )

    assert invitation.email == membership.user.email
    assert invitation.is_pending
    assert len(mail.outbox) == 1
    assert "https://civicflow.test" in mail.outbox[0].body


@pytest.mark.django_db
def test_resending_invitation_revokes_previous_attempt():
    membership = invited_membership()
    first = issue_staff_invitation(
        membership,
        invited_by=None,
        build_absolute_uri=lambda path: path,
    )
    second = issue_staff_invitation(
        membership,
        invited_by=None,
        build_absolute_uri=lambda path: path,
    )

    first.refresh_from_db()
    assert first.revoked_at is not None
    assert second.is_pending


@pytest.mark.django_db
def test_new_account_can_set_password_and_accept_invitation(client):
    membership = invited_membership()
    invitation = issue_staff_invitation(
        membership,
        invited_by=None,
        build_absolute_uri=lambda path: path,
    )

    response = client.post(
        invitation_path(invitation),
        {
            "new_password1": "A-long-safe-password-2026",
            "new_password2": "A-long-safe-password-2026",
        },
    )

    membership.refresh_from_db()
    invitation.refresh_from_db()
    membership.user.refresh_from_db()
    assert response.status_code == 302
    assert membership.status == TenantMembership.Status.ACTIVE
    assert membership.user.check_password("A-long-safe-password-2026")
    assert invitation.accepted_at is not None


@pytest.mark.django_db
def test_existing_account_accepts_without_resetting_password(client):
    membership = invited_membership(existing_account=True)
    original_password = membership.user.password
    invitation = issue_staff_invitation(
        membership,
        invited_by=None,
        build_absolute_uri=lambda path: path,
    )

    response = client.post(invitation_path(invitation))

    membership.refresh_from_db()
    membership.user.refresh_from_db()
    assert response.status_code == 302
    assert membership.status == TenantMembership.Status.ACTIVE
    assert membership.user.password == original_password


@pytest.mark.django_db
def test_revoked_invitation_is_rejected(client):
    membership = invited_membership()
    first = issue_staff_invitation(
        membership,
        invited_by=None,
        build_absolute_uri=lambda path: path,
    )
    issue_staff_invitation(
        membership,
        invited_by=None,
        build_absolute_uri=lambda path: path,
    )

    response = client.get(invitation_path(first))

    assert response.status_code == 400
    assert b"This invitation cannot be used" in response.content


@pytest.mark.django_db
def test_staff_can_suspend_and_reactivate_membership(client):
    staff = User.objects.create_user(email="admin@example.com", is_staff=True)
    membership = invited_membership(existing_account=True)
    membership.activate()
    client.force_login(staff)

    suspended = client.post(reverse("tenants:membership-suspend", args=(membership.pk,)))
    membership.refresh_from_db()
    assert suspended.status_code == 302
    assert membership.status == TenantMembership.Status.SUSPENDED

    reactivated = client.post(reverse("tenants:membership-activate", args=(membership.pk,)))
    membership.refresh_from_db()
    assert reactivated.status_code == 302
    assert membership.status == TenantMembership.Status.ACTIVE


@pytest.mark.django_db
def test_non_staff_cannot_change_membership_lifecycle(client):
    user = User.objects.create_user(email="ordinary@example.com")
    membership = invited_membership(existing_account=True)
    client.force_login(user)

    response = client.post(reverse("tenants:membership-activate", args=(membership.pk,)))

    assert response.status_code == 403
