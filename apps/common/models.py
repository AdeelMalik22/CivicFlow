from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ON_HOLD = "on-hold", "On hold"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="projects")
    name = models.CharField(max_length=200)
    reference = models.CharField(max_length=40)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    budget = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("tenant", "reference"), name="project_tenant_reference_unique")]

    def __str__(self):
        return f"{self.reference} — {self.name}"
