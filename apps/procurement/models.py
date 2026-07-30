from django.conf import settings
from django.db import models
from django.utils import timezone

class Tender(models.Model):
    class Category(models.TextChoices):
        WORKS = "works", "Works / construction"
        GOODS = "goods", "Goods / supplies"
        SERVICES = "services", "Professional services"

    class Method(models.TextChoices):
        OPEN = "open", "Open competition"
        LIMITED = "limited", "Limited competition"
        RFQ = "rfq", "Request for quotations"

    title = models.CharField(max_length=200)
    reference = models.CharField(max_length=40, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.WORKS)
    procurement_method = models.CharField(max_length=20, choices=Method.choices, default=Method.OPEN)
    department = models.ForeignKey("tenants.Department", null=True, blank=True, on_delete=models.PROTECT, related_name="tenders")
    service_area = models.ForeignKey("tenants.ServiceArea", null=True, blank=True, on_delete=models.PROTECT, related_name="tenders")
    budget = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default="PKR")
    eligibility = models.TextField(blank=True)
    evaluation_criteria = models.TextField(blank=True)
    submission_instructions = models.TextField(blank=True)
    clarification_deadline = models.DateTimeField(null=True, blank=True)
    contact_name = models.CharField(max_length=160, blank=True)
    contact_email = models.EmailField(blank=True)
    attachment = models.FileField(upload_to="tenders/%Y/%m/", blank=True)
    cover_image = models.FileField(upload_to="tenders/covers/%Y/%m/", blank=True)
    published = models.BooleanField(default=False)
    deadline = models.DateTimeField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.reference} — {self.title}"
    @property
    def open_for_bids(self): return self.published and self.deadline > timezone.now()

class Bid(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="bids")
    contractor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bids")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    proposal = models.TextField()
    document = models.FileField(upload_to="bids/%Y/%m/")
    submitted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("tender", "contractor"), name="one_bid_per_tender")]


class Award(models.Model):
    tender = models.OneToOneField(Tender, on_delete=models.PROTECT, related_name="award")
    winning_bid = models.OneToOneField(Bid, on_delete=models.PROTECT, related_name="award")
    awarded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decision_note = models.TextField(blank=True)
    awarded_at = models.DateTimeField(auto_now_add=True)


class ProcurementAuditEvent(models.Model):
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="audit_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ("-created_at",)
