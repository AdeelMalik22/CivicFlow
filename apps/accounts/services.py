from collections.abc import Callable

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.tenants.models import TenantMembership

from .models import StaffInvitation, User


class InvitationError(ValidationError):
    pass


def invitation_path(invitation: StaffInvitation) -> str:
    user = invitation.membership.user
    return reverse(
        "accounts:invitation-accept",
        kwargs={
            "public_id": invitation.public_id,
            "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
        },
    )


@transaction.atomic
def issue_staff_invitation(
    membership: TenantMembership,
    *,
    invited_by: User | None,
    build_absolute_uri: Callable[[str], str],
) -> StaffInvitation:
    membership = (
        TenantMembership.objects.select_for_update()
        .select_related("tenant", "user")
        .get(pk=membership.pk)
    )
    if membership.status != TenantMembership.Status.INVITED:
        raise InvitationError("Only invited memberships can receive an invitation.")

    now = timezone.now()
    membership.invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).update(
        revoked_at=now
    )
    invitation = StaffInvitation.objects.create(
        membership=membership,
        email=membership.user.email,
        invited_by=invited_by,
    )
    invitation_url = build_absolute_uri(invitation_path(invitation))
    recipient = invitation.email
    organization = membership.tenant.name
    inviter = str(invited_by) if invited_by else "A CivicFlow administrator"

    transaction.on_commit(
        lambda: send_mail(
            subject=f"You’re invited to {organization} on CivicFlow",
            message=(
                f"{inviter} invited you to join {organization} on CivicFlow.\n\n"
                f"Accept the invitation: {invitation_url}\n\n"
                "If you were not expecting this invitation, you can ignore this email."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
        )
    )
    return invitation


@transaction.atomic
def accept_staff_invitation(
    invitation: StaffInvitation,
    *,
    token: str,
    raw_password: str | None = None,
) -> TenantMembership:
    invitation = (
        StaffInvitation.objects.select_for_update()
        .select_related("membership__user", "membership__tenant")
        .get(pk=invitation.pk)
    )
    membership = invitation.membership
    user = membership.user

    if not invitation.is_pending:
        raise InvitationError("This invitation is no longer available.")
    if membership.status != TenantMembership.Status.INVITED:
        raise InvitationError("This membership is no longer awaiting activation.")
    if not default_token_generator.check_token(user, token):
        raise InvitationError("This invitation link is invalid or has expired.")
    if not user.has_usable_password():
        if not raw_password:
            raise InvitationError("Set a password to activate this account.")
        user.set_password(raw_password)
        user.is_active = True
        user.save(update_fields=("password", "is_active"))

    membership.activate()
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=("accepted_at",))
    membership.invitations.exclude(pk=invitation.pk).filter(
        accepted_at__isnull=True,
        revoked_at__isnull=True,
    ).update(revoked_at=timezone.now())
    return membership


@transaction.atomic
def suspend_membership(membership: TenantMembership) -> TenantMembership:
    membership = TenantMembership.objects.select_for_update().get(pk=membership.pk)
    if membership.status == TenantMembership.Status.SUSPENDED:
        return membership
    membership.suspend()
    membership.invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    return membership


@transaction.atomic
def activate_membership(membership: TenantMembership) -> TenantMembership:
    membership = TenantMembership.objects.select_for_update().get(pk=membership.pk)
    membership.activate()
    membership.invitations.filter(accepted_at__isnull=True, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
    return membership
