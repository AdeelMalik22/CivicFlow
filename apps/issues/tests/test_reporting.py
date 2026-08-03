import pytest
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.test import Client
from django.urls import reverse

from apps.issues.forms import IssueReportForm
from apps.issues.models import Issue, IssueInternalNote, IssueStatusEvent
from apps.tenants.models import ServiceArea, Tenant

User = get_user_model()


def service_area(name: str, tenant_name: str, slug: str) -> ServiceArea:
    tenant = Tenant.objects.create(
        name=tenant_name,
        slug=slug,
        status=Tenant.Status.ACTIVE,
    )
    return ServiceArea.objects.create(
        tenant=tenant,
        name=name,
        code=slug.upper(),
        boundary=MultiPolygon(Polygon.from_bbox((0, 0, 1, 1)), srid=4326),
    )


@pytest.mark.django_db
def test_report_form_rejects_location_outside_selected_service_area():
    area = service_area("Central", "City", "city")
    form = IssueReportForm(
        data={
            "service_area": area.pk,
            "category": Issue.Category.POTHOLE,
            "description": "A large pothole blocks the lane.",
            "location": "POINT (10 10)",
            "contact_preference": Issue.ContactPreference.NONE,
        }
    )

    assert not form.is_valid()
    assert "location" in form.errors


@pytest.mark.django_db
def test_anonymous_report_receives_reference_and_private_tracking_code(client: Client):
    area = service_area("Central", "City", "city")
    user = User.objects.create_user(
        email="citizen@example.com", password="pass", cnic="12345", email_verified=True
    )
    client.force_login(user)

    response = client.post(
        reverse("issues:report"),
        {
            "service_area": area.pk,
            "category": Issue.Category.POTHOLE,
            "description": "A large pothole blocks the lane.",
            "location": "POINT (0.5 0.5)",
            "contact_preference": Issue.ContactPreference.NONE,
        },
    )

    issue = Issue.objects.get()
    assert response.status_code == 302
    assert issue.reference in response.url
    assert issue.status == Issue.Status.SUBMITTED
    assert IssueStatusEvent.objects.filter(issue=issue).count() == 1
    token = response.url.rstrip("/").split("/")[-1]
    assert issue.check_tracking_token(token)


@pytest.mark.django_db
def test_public_tracking_requires_correct_verification_code(client: Client):
    area = service_area("Central", "City", "city")
    report = IssueReportForm(
        data={
            "service_area": area.pk,
            "category": Issue.Category.DRAINAGE,
            "description": "The drain is blocked.",
            "location": "POINT (0.5 0.5)",
            "contact_preference": Issue.ContactPreference.NONE,
        }
    )
    assert report.is_valid()

    response = client.post(reverse("issues:track-lookup"), {
        "reference": "CF-20260730-ABC123",
        "verification_code": "not-valid",
    })

    assert response.status_code == 200
    assert b"could not verify" in response.content


@pytest.mark.django_db
def test_public_tracking_does_not_expose_contact_details(client: Client):
    area = service_area("Central", "City", "city")
    issue = Issue(
        reference="CF-20260730-ABC123",
        tenant=area.tenant,
        service_area=area,
        category=Issue.Category.SIDEWALK,
        description="Broken sidewalk.",
        location=Point(0.5, 0.5, srid=4326),
        contact_email="private@example.com",
    )
    issue.set_tracking_token("private-token")
    issue.save()
    IssueStatusEvent.objects.create(
        issue=issue,
        status=Issue.Status.SUBMITTED,
        public_message="Your report was received.",
    )

    response = client.get(
        reverse(
            "issues:track",
            kwargs={"reference": issue.reference, "token": "private-token"},
        )
    )

    assert response.status_code == 200
    assert b"private@example.com" not in response.content
    assert b"Broken sidewalk." not in response.content


@pytest.mark.django_db
def test_report_form_rejects_point_inside_bbox_but_outside_polygon():
    tenant = Tenant.objects.create(name="City", slug="polygon-city", status=Tenant.Status.ACTIVE)
    area = ServiceArea.objects.create(
        tenant=tenant, name="Concave", code="CONCAVE",
        boundary=MultiPolygon(Polygon((0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2), (0, 0), srid=4326)),
    )
    form = IssueReportForm(data={"service_area": area.pk, "category": Issue.Category.OTHER, "description": "Blocked access.", "location": "POINT (1.5 1.5)", "contact_preference": Issue.ContactPreference.NONE})
    assert not form.is_valid()
    assert "location" in form.errors


@pytest.mark.django_db
def test_staff_update_assigns_department_and_creates_private_note(client: Client):
    area = service_area("Central", "City", "assign-city")
    staff = User.objects.create_user(email="staff@example.com", password="pass", is_staff=True)
    department = area.tenant.departments.create(name="Roads", code="ROADS")
    issue = Issue.objects.create(reference="CF-20260730-ASSIGN", tenant=area.tenant, service_area=area, category=Issue.Category.POTHOLE, description="Pothole", location=Point(.5, .5, srid=4326), tracking_token_hash="x")
    client.force_login(staff)
    response = client.post(reverse("issues:report_detail", kwargs={"pk": issue.pk}), {"status": Issue.Status.UNDER_REVIEW, "assigned_to": staff.pk, "assigned_department": department.pk, "public_message": "Team assigned.", "internal_note": "Inspect before dispatch."})
    assert response.status_code == 302
    issue.refresh_from_db()
    assert issue.assigned_to_id == staff.pk and issue.assigned_department_id == department.pk
    assert IssueInternalNote.objects.filter(issue=issue, body="Inspect before dispatch.").exists()


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_status_change_sends_email_notification(client: Client):
    area = service_area("Central", "City", "email-city")
    staff = User.objects.create_user(email="staff@example.com", password="pass", is_staff=True)
    issue = Issue.objects.create(reference="CF-20260730-EMAIL", tenant=area.tenant, service_area=area, category=Issue.Category.POTHOLE, description="Pothole", location=Point(.5, .5, srid=4326), contact_email="citizen@example.com", contact_preference=Issue.ContactPreference.EMAIL, tracking_token_hash="x")
    client.force_login(staff)
    client.post(reverse("issues:report_detail", kwargs={"pk": issue.pk}), {"status": Issue.Status.CLOSED, "public_message": "The repair is complete."})
    assert len(mail.outbox) == 1
    assert issue.reference in mail.outbox[0].subject


@pytest.mark.django_db
def test_tracking_lookup_is_rate_limited(client: Client):
    cache.clear()
    for _ in range(10):
        client.post(reverse("issues:track-lookup"), {"reference": "CF-NOT-FOUND", "verification_code": "bad"})
    response = client.post(reverse("issues:track-lookup"), {"reference": "CF-NOT-FOUND", "verification_code": "bad"})
    assert response.status_code == 200
    assert b"Too many verification attempts" in response.content
