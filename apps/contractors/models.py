from django.conf import settings
from django.db import models


class ContractorApplication(models.Model):
    class Status(models.TextChoices):
        PENDING_REVIEW = "pending_review", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        INFO_REQUESTED = "info_requested", "Information requested"
        SUSPENDED = "suspended", "Suspended"
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contractor_applications")
    company_name = models.CharField(max_length=180)
    registration_number = models.CharField(max_length=120)
    contact_person = models.CharField(max_length=150)
    phone = models.CharField(max_length=32)
    cnic_ntn = models.CharField(max_length=64)
    category = models.CharField(max_length=120)
    years_experience = models.PositiveSmallIntegerField()
    registration_document = models.FileField(upload_to="contractors/%Y/%m/")
    tax_document = models.FileField(upload_to="contractors/%Y/%m/")
    cnic_document = models.FileField(upload_to="contractors/%Y/%m/")
    references_document = models.FileField(upload_to="contractors/%Y/%m/", blank=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.PENDING_REVIEW)
    review_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="contractor_reviews")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
