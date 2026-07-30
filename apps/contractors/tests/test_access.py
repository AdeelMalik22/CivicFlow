import pytest

from apps.accounts.models import User
from apps.contractors.access import can_submit_bids
from apps.contractors.models import ContractorApplication

def application(user, status):
    return ContractorApplication.objects.create(applicant=user, company_name="Co", registration_number="R", contact_person="A", phone="1", cnic_ntn="2", category="roads", years_experience=1, registration_document="r", tax_document="t", cnic_document="c", status=status)

@pytest.mark.django_db
@pytest.mark.parametrize("status", ["pending_review", "rejected", "info_requested", "suspended"])
def test_non_approved_contractors_cannot_bid(status):
    user = User.objects.create_user(email="x@example.com", password="pass")
    application(user, status)
    assert not can_submit_bids(user)

@pytest.mark.django_db
def test_inactive_user_cannot_bid_even_when_approved():
    user = User.objects.create_user(email="x@example.com", password="pass", is_active=False)
    application(user, "approved")
    assert not can_submit_bids(user)
