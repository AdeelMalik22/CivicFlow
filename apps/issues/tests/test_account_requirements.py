import pytest
from apps.accounts.models import User
from apps.issues.forms import IssueReportForm
from apps.issues.models import Issue
from .test_reporting import service_area

@pytest.mark.django_db
def test_report_requires_cnic_for_verified_user():
    user = User.objects.create_user(email="citizen@example.com", password="pass", email_verified=True)
    area = service_area("Central", "City", "city")
    form = IssueReportForm(data={"service_area": area.pk, "category": Issue.Category.OTHER, "description": "Issue", "location": "POINT (0.5 0.5)", "contact_preference": "none"}, user=user)
    assert not form.is_valid()
    assert "CNIC" in str(form.errors)
