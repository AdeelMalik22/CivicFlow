import hashlib
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from apps.tenants.scoping import TenantScopedQuerySet

from .managers import UserManager


class User(AbstractUser):
    """CivicFlow user identified by email instead of a username."""

    username = None
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField("email address", unique=True)
    phone_number = models.CharField(max_length=32, blank=True)
    cnic = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255, blank=True)
    email_verified = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.get_full_name() or self.email


class SignupOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="signup_otps")
    code_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Signup OTP for {self.user.email}"

    def verify_code(self, code: str) -> bool:
        self.attempts += 1
        self.save(update_fields=("attempts",))
        digest = hashlib.sha256(code.encode()).hexdigest()
        return self.attempts <= 5 and self.expires_at > timezone.now() and digest == self.code_hash


class AccessPermission(models.Model):
    """A stable capability that can be granted to a tenant role."""

    class Scope(models.TextChoices):
        OWN = "own", "Own records"
        ASSIGNED = "assigned", "Assigned records"
        TENANT = "tenant", "Entire organization"

    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=240, blank=True)
    default_scope = models.CharField(max_length=16, choices=Scope, default=Scope.TENANT)
    is_sensitive = models.BooleanField(default=False)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class TenantRole(models.Model):
    """A configurable role belonging to exactly one CivicFlow tenant."""

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="roles",
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=40)
    description = models.CharField(max_length=240, blank=True)
    requires_mfa = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(
        AccessPermission,
        through="RolePermission",
        related_name="roles",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedQuerySet.as_manager()

    class Meta:
        ordering = ("tenant__name", "name")
        constraints = [
            models.UniqueConstraint(
                Lower("code"),
                models.F("tenant"),
                name="role_tenant_code_ci_unique",
            ),
            models.UniqueConstraint(
                Lower("name"),
                models.F("tenant"),
                name="role_tenant_name_ci_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant.name})"

    def save(self, *args, **kwargs) -> None:
        self.code = self.code.lower()
        super().save(*args, **kwargs)


class RolePermission(models.Model):
    role = models.ForeignKey(TenantRole, on_delete=models.CASCADE, related_name="grants")
    permission = models.ForeignKey(
        AccessPermission,
        on_delete=models.PROTECT,
        related_name="grants",
    )
    scope = models.CharField(max_length=16, choices=AccessPermission.Scope)

    class Meta:
        ordering = ("permission__name",)
        constraints = [
            models.UniqueConstraint(
                fields=("role", "permission"),
                name="role_permission_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.role.name}: {self.permission.name}"


class MembershipRole(models.Model):
    membership = models.ForeignKey(
        "tenants.TenantMembership",
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.ForeignKey(
        TenantRole,
        on_delete=models.PROTECT,
        related_name="membership_assignments",
    )
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="role_assignments_made",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("membership", "role"),
                name="membership_role_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.membership} — {self.role.name}"

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if (
            self.membership_id
            and self.role_id
            and self.membership.tenant_id != self.role.tenant_id
        ):
            raise ValidationError("Membership and role must belong to the same organization.")


class SeparationOfDutiesPolicy(models.Model):
    """Prevent the same actor from initiating and approving a sensitive action."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="separation_policies",
    )
    name = models.CharField(max_length=120)
    initiator_permission = models.ForeignKey(
        AccessPermission,
        on_delete=models.PROTECT,
        related_name="initiator_policies",
    )
    approver_permission = models.ForeignKey(
        AccessPermission,
        on_delete=models.PROTECT,
        related_name="approver_policies",
    )
    is_active = models.BooleanField(default=True)

    objects = TenantScopedQuerySet.as_manager()

    class Meta:
        ordering = ("tenant__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "initiator_permission", "approver_permission"),
                name="tenant_sod_policy_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant.name})"

    def clean(self) -> None:
        super().clean()
        if self.initiator_permission_id == self.approver_permission_id:
            raise ValidationError(
                "Initiator and approver permissions must be different capabilities."
            )


class StaffInvitation(models.Model):
    """One auditable delivery attempt for a tenant membership invitation."""

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    membership = models.ForeignKey(
        "tenants.TenantMembership",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_invitations_sent",
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-sent_at",)
        indexes = [
            models.Index(
                fields=("membership", "accepted_at", "revoked_at"),
                name="invite_membership_state_idx",
            )
        ]

    def __str__(self) -> str:
        return f"{self.email} — {self.membership.tenant.name}"

    @property
    def is_pending(self) -> bool:
        return self.accepted_at is None and self.revoked_at is None
