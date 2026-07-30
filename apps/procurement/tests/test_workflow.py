from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail

from apps.accounts.models import User
from apps.contractors.models import ContractorApplication
from apps.procurement.models import Award, Bid, ProcurementAuditEvent, Tender


@pytest.fixture
def contractor(db):
    return User.objects.create_user(email="builder@example.com", password="pass")


@pytest.fixture
def tender(db):
    staff = User.objects.create_user(email="officer@example.gov", password="pass", is_staff=True)
    return Tender.objects.create(
        title="Road repair", reference="TN-001", description="Repair road",
        published=True, deadline=timezone.now() + timedelta(days=1), created_by=staff,
    )


def approve(user):
    return ContractorApplication.objects.create(
        applicant=user, company_name="Builder", registration_number="REG-1",
        contact_person="Builder", phone="1", cnic_ntn="2", category="roads",
        years_experience=3, registration_document="x", tax_document="x", cnic_document="x",
        status=ContractorApplication.Status.APPROVED,
    )


@pytest.mark.django_db
def test_unapproved_contractor_cannot_bid(client, contractor, tender):
    client.force_login(contractor)
    response = client.get(reverse("procurement:bid", args=[tender.pk]))
    assert response.status_code == 302
    assert not Bid.objects.exists()


@pytest.mark.django_db
def test_approved_contractor_can_submit_one_bid(client, contractor, tender):
    approve(contractor)
    client.force_login(contractor)
    payload = {
        "amount": Decimal("1000"),
        "proposal": "Ready",
        "document": SimpleUploadedFile("bid.pdf", b"bid", content_type="application/pdf"),
    }
    response = client.post(reverse("procurement:bid", args=[tender.pk]), payload)
    assert response.status_code == 302
    assert Bid.objects.filter(tender=tender, contractor=contractor).count() == 1


@pytest.mark.django_db
def test_award_creates_audit_and_closes_tender(client, contractor, tender):
    approve(contractor)
    bid = Bid.objects.create(tender=tender, contractor=contractor, amount=100, proposal="x", document="x")
    client.force_login(tender.created_by)
    response = client.post(reverse("procurement:award", args=[tender.pk]), {"winning_bid": bid.pk, "decision_note": "Best value"})
    assert response.status_code == 302
    assert Award.objects.filter(tender=tender).exists()
    assert ProcurementAuditEvent.objects.filter(tender=tender, action="award_finalized").exists()
    tender.refresh_from_db()
    assert tender.published is False
    assert len(mail.outbox) == 1
    assert contractor.email in mail.outbox[0].to
