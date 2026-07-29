import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower


def validate_timezone(value: str) -> None:
    """Ensure tenant timezones use a recognized IANA identifier."""
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValidationError(
            "%(value)s is not a recognized IANA timezone.",
            params={"value": value},
        ) from exc


department_code_validator = RegexValidator(
    regex=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
    message="Use letters, numbers, hyphens, or underscores, starting with a letter or number.",
)

service_area_code_validator = RegexValidator(
    regex=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
    message="Use letters, numbers, hyphens, or underscores, starting with a letter or number.",
)


class Tenant(models.Model):
    """A government organization or jurisdiction isolated within CivicFlow."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending setup"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=180)
    slug = models.SlugField(
        max_length=80,
        help_text="Stable identifier used in tenant-scoped URLs and integrations.",
    )
    status = models.CharField(max_length=16, choices=Status, default=Status.PENDING)
    timezone = models.CharField(
        max_length=64,
        default="UTC",
        validators=[validate_timezone],
        help_text="IANA timezone, for example Asia/Karachi.",
    )
    default_language = models.CharField(max_length=10, default="en")
    contact_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                Lower("slug"),
                name="tenant_slug_ci_unique",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        self.slug = self.slug.lower()
        super().save(*args, **kwargs)


class Department(models.Model):
    """An operational unit belonging to exactly one tenant."""

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="departments",
    )
    name = models.CharField(max_length=120)
    code = models.CharField(
        max_length=30,
        validators=[department_code_validator],
        help_text="Tenant-unique short code, for example ROADS or WASTE.",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("tenant__name", "name")
        constraints = [
            models.UniqueConstraint(
                Lower("code"),
                models.F("tenant"),
                name="dept_tenant_code_ci_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "is_active"),
                name="dept_tenant_active_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant.name})"

    def save(self, *args, **kwargs) -> None:
        self.code = self.code.upper()
        super().save(*args, **kwargs)


class ServiceAreaQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, tenant__status=Tenant.Status.ACTIVE)

    def covering(self, point: Point, *, tenant: Tenant | None = None):
        queryset = self.active().filter(boundary__covers=point)
        if tenant is not None:
            queryset = queryset.filter(tenant=tenant)
        return queryset


class ServiceArea(models.Model):
    """A tenant-owned geographic boundary used to route public reports."""

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="service_areas",
    )
    name = models.CharField(max_length=140)
    code = models.CharField(
        max_length=30,
        validators=[service_area_code_validator],
        help_text="Tenant-unique short code, for example CENTRAL or NORTH-01.",
    )
    description = models.TextField(blank=True)
    boundary = gis_models.MultiPolygonField(
        srid=4326,
        help_text="The supported boundary in WGS 84 coordinates.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ServiceAreaQuerySet.as_manager()

    class Meta:
        ordering = ("tenant__name", "name")
        constraints = [
            models.UniqueConstraint(
                Lower("code"),
                models.F("tenant"),
                name="area_tenant_code_ci_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "is_active"),
                name="area_tenant_active_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant.name})"

    def save(self, *args, **kwargs) -> None:
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.boundary and (self.boundary.empty or not self.boundary.valid):
            raise ValidationError({"boundary": "Enter a non-empty, valid multipolygon boundary."})
