import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import Client
from django.urls import reverse

from apps.tenants.models import Department, ServiceArea, Tenant

User = get_user_model()


@pytest.mark.django_db
def test_tenant_directory_requires_staff(client: Client):
    user = User.objects.create_user(
        email="citizen@example.com",
        password="a-safe-test-password",
    )
    client.force_login(user)

    response = client.get(reverse("tenants:list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_can_view_tenants_and_department_counts(client: Client):
    staff = User.objects.create_user(
        email="staff@example.com",
        password="a-safe-test-password",
        is_staff=True,
    )
    tenant = Tenant.objects.create(
        name="Metropolitan Services",
        slug="metropolitan-services",
        status=Tenant.Status.ACTIVE,
    )
    Department.objects.create(tenant=tenant, name="Roads", code="ROADS")
    Department.objects.create(
        tenant=tenant,
        name="Archived Unit",
        code="ARCHIVE",
        is_active=False,
    )
    client.force_login(staff)

    response = client.get(reverse("tenants:list"))

    assert response.status_code == 200
    assert b"Metropolitan Services" in response.content
    assert response.context["tenants"][0].department_count == 2
    assert response.context["tenants"][0].active_department_count == 1


@pytest.mark.django_db
def test_service_area_directory_requires_staff(client: Client):
    user = User.objects.create_user(
        email="citizen@example.com",
        password="a-safe-test-password",
    )
    client.force_login(user)

    response = client.get(reverse("tenants:service-area-list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_can_view_service_area_directory(client: Client):
    staff = User.objects.create_user(
        email="staff@example.com",
        password="a-safe-test-password",
        is_staff=True,
    )
    tenant = Tenant.objects.create(
        name="Metropolitan Services",
        slug="metropolitan-services",
        status=Tenant.Status.ACTIVE,
    )
    boundary = MultiPolygon(Polygon.from_bbox((0, 0, 1, 1)), srid=4326)
    ServiceArea.objects.create(
        tenant=tenant,
        name="Central District",
        code="CENTRAL",
        boundary=boundary,
    )
    client.force_login(staff)

    response = client.get(reverse("tenants:service-area-list"))

    assert response.status_code == 200
    assert b"Central District" in response.content
    assert b"Metropolitan Services" in response.content
    assert response.context["active_area_count"] == 1
    assert response.context["tenant_count"] == 1
