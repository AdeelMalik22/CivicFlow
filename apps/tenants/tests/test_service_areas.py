import pytest
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.tenants.models import ServiceArea, Tenant


def service_boundary(*, offset: float = 0) -> MultiPolygon:
    polygon = Polygon.from_bbox((offset, offset, offset + 1, offset + 1))
    return MultiPolygon(polygon, srid=4326)


@pytest.mark.django_db
def test_service_area_normalizes_code_and_preserves_spatial_reference():
    tenant = Tenant.objects.create(
        name="Metropolitan Services",
        slug="metropolitan-services",
        status=Tenant.Status.ACTIVE,
    )

    area = ServiceArea.objects.create(
        tenant=tenant,
        name="Central District",
        code="central-01",
        boundary=service_boundary(),
    )

    assert area.code == "CENTRAL-01"
    assert area.boundary.srid == 4326
    assert area.boundary.valid


@pytest.mark.django_db
def test_service_area_rejects_invalid_boundary():
    tenant = Tenant.objects.create(name="Example", slug="example")
    crossed_polygon = Polygon(
        ((0, 0), (1, 1), (1, 0), (0, 1), (0, 0)),
        srid=4326,
    )
    area = ServiceArea(
        tenant=tenant,
        name="Invalid",
        code="INVALID",
        boundary=MultiPolygon(crossed_polygon, srid=4326),
    )

    with pytest.raises(ValidationError) as error:
        area.full_clean()

    assert "boundary" in error.value.message_dict


@pytest.mark.django_db
def test_service_area_code_is_unique_within_tenant():
    tenant = Tenant.objects.create(name="Example", slug="example")
    ServiceArea.objects.create(
        tenant=tenant,
        name="Central",
        code="central",
        boundary=service_boundary(),
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ServiceArea.objects.create(
            tenant=tenant,
            name="Duplicate",
            code="CENTRAL",
            boundary=service_boundary(offset=2),
        )


@pytest.mark.django_db
def test_covering_returns_only_active_area_for_requested_tenant():
    first_tenant = Tenant.objects.create(
        name="First",
        slug="first",
        status=Tenant.Status.ACTIVE,
    )
    second_tenant = Tenant.objects.create(
        name="Second",
        slug="second",
        status=Tenant.Status.ACTIVE,
    )
    expected = ServiceArea.objects.create(
        tenant=first_tenant,
        name="First Central",
        code="CENTRAL",
        boundary=service_boundary(),
    )
    ServiceArea.objects.create(
        tenant=second_tenant,
        name="Second Central",
        code="CENTRAL",
        boundary=service_boundary(),
    )
    ServiceArea.objects.create(
        tenant=first_tenant,
        name="Inactive",
        code="INACTIVE",
        boundary=service_boundary(),
        is_active=False,
    )

    matches = ServiceArea.objects.covering(
        Point(0.5, 0.5, srid=4326),
        tenant=first_tenant,
    )

    assert list(matches) == [expected]


@pytest.mark.django_db
def test_covering_does_not_match_point_outside_boundary():
    tenant = Tenant.objects.create(
        name="Example",
        slug="example",
        status=Tenant.Status.ACTIVE,
    )
    ServiceArea.objects.create(
        tenant=tenant,
        name="Central",
        code="CENTRAL",
        boundary=service_boundary(),
    )

    assert not ServiceArea.objects.covering(
        Point(10, 10, srid=4326),
        tenant=tenant,
    ).exists()
