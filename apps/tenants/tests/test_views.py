import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.test import Client
from django.urls import reverse

from apps.tenants.models import Department, ServiceArea, Tenant, TenantMembership

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
    first_member = User.objects.create_user(email="first-member@example.com")
    second_member = User.objects.create_user(email="second-member@example.com")
    TenantMembership.objects.create(
        tenant=tenant,
        user=first_member,
        status=TenantMembership.Status.ACTIVE,
    )
    TenantMembership.objects.create(
        tenant=tenant,
        user=second_member,
        status=TenantMembership.Status.INVITED,
    )
    client.force_login(staff)

    response = client.get(reverse("tenants:list"))

    assert response.status_code == 200
    assert b"Metropolitan Services" in response.content
    assert response.context["tenants"][0].department_count == 2
    assert response.context["tenants"][0].active_department_count == 1
    assert response.context["tenants"][0].membership_count == 2
    assert response.context["tenants"][0].active_membership_count == 1


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


@pytest.mark.django_db
def test_membership_directory_requires_staff(client: Client):
    user = User.objects.create_user(
        email="citizen@example.com",
        password="a-safe-test-password",
    )
    client.force_login(user)

    response = client.get(reverse("tenants:membership-list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_staff_can_view_membership_directory(client: Client):
    staff = User.objects.create_user(
        email="staff@example.com",
        password="a-safe-test-password",
        is_staff=True,
    )
    member = User.objects.create_user(
        email="officer@example.com",
        first_name="Aisha",
        last_name="Khan",
    )
    tenant = Tenant.objects.create(
        name="Metropolitan Services",
        slug="metropolitan-services",
        status=Tenant.Status.ACTIVE,
    )
    TenantMembership.objects.create(
        tenant=tenant,
        user=member,
        invited_by=staff,
        status=TenantMembership.Status.ACTIVE,
    )
    client.force_login(staff)

    response = client.get(reverse("tenants:membership-list"))

    assert response.status_code == 200
    assert b"Aisha Khan" in response.content
    assert b"Metropolitan Services" in response.content
    assert response.context["active_membership_count"] == 1
    assert response.context["invited_membership_count"] == 0
    assert response.context["tenant_count"] == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name",
    ("tenants:add", "tenants:service-area-add", "tenants:membership-add"),
)
def test_entity_forms_require_staff(client: Client, url_name: str):
    user = User.objects.create_user(email="citizen@example.com")
    client.force_login(user)

    assert client.get(reverse(url_name)).status_code == 403


@pytest.mark.django_db
def test_staff_can_add_and_edit_organization_in_workspace(client: Client):
    staff = User.objects.create_user(email="staff@example.com", is_staff=True)
    client.force_login(staff)

    response = client.post(
        reverse("tenants:add"),
        {
            "name": "City Services",
            "slug": "City-Services",
            "status": Tenant.Status.ACTIVE,
            "timezone": "Asia/Karachi",
            "default_language": "en",
            "contact_email": "contact@example.com",
        },
    )

    tenant = Tenant.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("tenants:list")
    assert tenant.slug == "city-services"
    list_page = client.get(reverse("tenants:list")).content.decode()
    assert reverse("tenants:edit", args=(tenant.pk,)) in list_page


@pytest.mark.django_db
def test_staff_can_add_membership_and_inviter_is_recorded(client: Client):
    staff = User.objects.create_user(email="staff@example.com", is_staff=True)
    member = User.objects.create_user(email="member@example.com")
    tenant = Tenant.objects.create(name="City Services", slug="city-services")
    client.force_login(staff)

    response = client.post(
        reverse("tenants:membership-add"),
        {"tenant": tenant.pk, "user": member.pk, "status": TenantMembership.Status.INVITED},
    )

    membership = TenantMembership.objects.get()
    assert response.status_code == 302
    assert membership.invited_by == staff


@pytest.mark.django_db
def test_staff_can_add_service_area_with_map_boundary(client: Client):
    staff = User.objects.create_user(email="staff@example.com", is_staff=True)
    tenant = Tenant.objects.create(
        name="City Services",
        slug="city-services",
        status=Tenant.Status.ACTIVE,
    )
    client.force_login(staff)

    form_page = client.get(reverse("tenants:service-area-add"))
    assert form_page.status_code == 200
    assert b'id="id_boundary_map"' in form_page.content
    assert b"OLMapWidget.js" in form_page.content

    response = client.post(
        reverse("tenants:service-area-add"),
        {
            "tenant": tenant.pk,
            "name": "Central District",
            "code": "central",
            "description": "Central service boundary",
            "boundary": "MULTIPOLYGON (((0 0, 0 1, 1 1, 1 0, 0 0)))",
            "is_active": "on",
        },
    )

    area = ServiceArea.objects.get()
    assert response.status_code == 302
    assert response.url == reverse("tenants:service-area-list")
    assert area.code == "CENTRAL"
    assert area.boundary.srid == 4326


@pytest.mark.django_db
def test_operational_lists_do_not_link_to_django_admin(client: Client):
    staff = User.objects.create_user(email="staff@example.com", is_staff=True)
    tenant = Tenant.objects.create(name="City Services", slug="city-services")
    member = User.objects.create_user(email="member@example.com")
    TenantMembership.objects.create(tenant=tenant, user=member)
    boundary = MultiPolygon(Polygon.from_bbox((0, 0, 1, 1)), srid=4326)
    ServiceArea.objects.create(
        tenant=tenant,
        name="Central",
        code="CENTRAL",
        boundary=boundary,
    )
    client.force_login(staff)

    for url_name in (
        "tenants:list",
        "tenants:service-area-list",
        "tenants:membership-list",
    ):
        response = client.get(reverse(url_name))
        assert b"/admin/tenants/" not in response.content
