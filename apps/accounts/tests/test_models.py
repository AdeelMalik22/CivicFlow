import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_normalizes_email_and_has_public_id():
    user = User.objects.create_user(
        email="Citizen@EXAMPLE.COM",
        password="a-safe-test-password",
    )

    assert user.email == "citizen@example.com"
    assert user.public_id is not None
    assert user.check_password("a-safe-test-password")
    assert not user.is_staff
    assert not user.is_superuser


@pytest.mark.django_db
def test_create_user_requires_email():
    with pytest.raises(ValueError, match="email address"):
        User.objects.create_user(email="", password="a-safe-test-password")


@pytest.mark.django_db
def test_create_superuser_sets_required_flags():
    user = User.objects.create_superuser(
        email="admin@example.com",
        password="a-safe-test-password",
    )

    assert user.is_staff
    assert user.is_superuser
