import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError

from apps.tenants.models import Department, Tenant


@pytest.mark.django_db
def test_tenant_normalizes_slug_and_accepts_iana_timezone():
    tenant = Tenant.objects.create(
        name="Metropolitan Services",
        slug="METRO-Services",
        status=Tenant.Status.ACTIVE,
        timezone="Asia/Karachi",
    )

    assert tenant.slug == "metro-services"
    tenant.full_clean()


@pytest.mark.django_db
def test_tenant_rejects_unknown_timezone():
    tenant = Tenant(name="Example", slug="example", timezone="Planet/Unknown")

    with pytest.raises(ValidationError) as error:
        tenant.full_clean()

    assert "timezone" in error.value.message_dict


@pytest.mark.django_db(transaction=True)
def test_tenant_slug_is_case_insensitively_unique():
    Tenant.objects.create(name="First", slug="civic-authority")

    with pytest.raises(IntegrityError):
        Tenant.objects.create(name="Second", slug="CIVIC-AUTHORITY")


@pytest.mark.django_db
def test_department_normalizes_code_and_is_unique_within_tenant():
    first_tenant = Tenant.objects.create(name="First", slug="first")
    second_tenant = Tenant.objects.create(name="Second", slug="second")

    department = Department.objects.create(
        tenant=first_tenant,
        name="Road Maintenance",
        code="roads",
    )
    Department.objects.create(
        tenant=second_tenant,
        name="Road Maintenance",
        code="roads",
    )

    assert department.code == "ROADS"
    with pytest.raises(IntegrityError):
        Department.objects.create(
            tenant=first_tenant,
            name="Other Roads",
            code="roads",
        )


@pytest.mark.django_db
def test_tenant_with_departments_cannot_be_deleted():
    tenant = Tenant.objects.create(name="Protected", slug="protected")
    Department.objects.create(tenant=tenant, name="Operations", code="OPS")

    with pytest.raises(ProtectedError):
        tenant.delete()
