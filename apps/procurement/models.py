from django.conf import settings
from django.db import models
from django.utils import timezone

class Tender(models.Model):
    title = models.CharField(max_length=200)
    reference = models.CharField(max_length=40, unique=True)
    description = models.TextField()
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
