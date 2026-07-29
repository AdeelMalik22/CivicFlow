import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

User = get_user_model()


def test_sign_in_page_uses_email_field(client: Client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b"Staff sign in" in response.content
    assert b'type="email"' in response.content


@pytest.mark.django_db
def test_user_can_sign_in_and_sign_out(client: Client):
    user = User.objects.create_user(
        email="officer@example.com",
        password="a-safe-test-password",
    )

    response = client.post(
        reverse("login"),
        {
            "username": user.email,
            "password": "a-safe-test-password",
        },
    )

    assert response.status_code == 302
    assert response.url == reverse("home")

    home_response = client.get(reverse("home"))
    assert b"officer@example.com" in home_response.content

    logout_response = client.post(reverse("logout"))
    assert logout_response.status_code == 302
    assert logout_response.url == reverse("home")
