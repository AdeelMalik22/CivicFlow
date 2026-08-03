import hashlib
import secrets
import uuid

from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.utils import timezone

from apps.tenants.models import Department, ServiceArea, Tenant


class Issue(models.Model):
    class Category(models.TextChoices):
        POTHOLE = "pothole", "Pothole or road damage"
        STREETLIGHT = "streetlight", "Streetlight or signal"
        DRAINAGE = "drainage", "Blocked drain or flooding"
        SIDEWALK = "sidewalk", "Sidewalk or accessibility"
        PUBLIC_BUILDING = "public-building", "Public building"
        OTHER = "other", "Other infrastructure issue"

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under-review", "Under review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        DUPLICATE = "duplicate", "Duplicate"
        CLOSED = "closed", "Closed"

    class ContactPreference(models.TextChoices):
        EMAIL = "email", "Email updates"
        NONE = "none", "No updates"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reference = models.CharField(max_length=24, unique=True, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="issues")
    service_area = models.ForeignKey(
        ServiceArea,
        on_delete=models.PROTECT,
        related_name="issues",
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reported_issues",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_issues",
    )
    assigned_department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_issues",
    )
    category = models.CharField(max_length=32, choices=Category)
    description = models.TextField(max_length=4000)
    location = gis_models.PointField(srid=4326)
    contact_email = models.EmailField(blank=True)
    contact_preference = models.CharField(
        max_length=12,
        choices=ContactPreference,
        default=ContactPreference.NONE,
    )
    status = models.CharField(max_length=24, choices=Status, default=Status.SUBMITTED)
    tracking_token_hash = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("tenant", "status", "created_at"), name="issue_tenant_status_idx"),
            models.Index(fields=("reference",), name="issue_reference_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.reference} — {self.get_category_display()}"

    def set_tracking_token(self, token: str) -> None:
        self.tracking_token_hash = hashlib.sha256(token.encode()).hexdigest()

    def check_tracking_token(self, token: str) -> bool:
        digest = hashlib.sha256(token.encode()).hexdigest()
        return secrets.compare_digest(self.tracking_token_hash, digest)

    def clean(self) -> None:
        super().clean()
        if (
            self.service_area_id
            and self.tenant_id
            and self.service_area.tenant_id != self.tenant_id
        ):
            raise ValidationError("The service area must belong to the issue organization.")
        if (
            self.location
            and self.service_area_id
            and not self.service_area.boundary.covers(self.location)
        ):
            raise ValidationError(
                {"location": "The location must be inside the selected service area."}
            )
        if self.contact_email:
            validate_email(self.contact_email)


class IssueStatusEvent(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="status_events")
    status = models.CharField(max_length=24, choices=Issue.Status)
    public_message = models.CharField(max_length=500)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="issue_status_events",
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.issue.reference}: {self.get_status_display()}"


class IssueInternalNote(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="internal_notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="issue_internal_notes")
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)


def create_tracking_token() -> str:
    return secrets.token_urlsafe(24)


class IssueAttachment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="issue-evidence/%Y/%m/")
    original_name = models.CharField(max_length=255)
    checksum = models.CharField(max_length=64, editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="issue_attachments",
    )

    class Meta:
        ordering = ("uploaded_at",)

    def __str__(self) -> str:
        return f"{self.issue.reference}: {self.original_name}"
