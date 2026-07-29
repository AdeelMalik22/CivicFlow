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


def test_workspace_requires_authentication(client: Client):
    response = client.get(reverse("workspace"))

    assert response.status_code == 302
    assert response.url == f"{reverse('login')}?next={reverse('workspace')}"


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
    assert response.url == reverse("workspace")

    workspace_response = client.get(reverse("workspace"))
    assert workspace_response.status_code == 200
    assert b"officer@example.com" in workspace_response.content
    assert b"Core platform services are ready" in workspace_response.content

    logout_response = client.post(reverse("logout"))
    assert logout_response.status_code == 302
    assert logout_response.url == reverse("home")


def test_unknown_page_uses_branded_not_found_template(client: Client, settings):
    settings.DEBUG = False

    response = client.get("/this-page-does-not-exist/")

    assert response.status_code == 404
    assert b"We couldn\xe2\x80\x99t find the page you requested." in response.content
