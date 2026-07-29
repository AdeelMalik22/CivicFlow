import uuid
from unittest.mock import patch

import pytest
from django.db import connections
from django.db.utils import OperationalError
from django.test import Client


def test_liveness_is_public_and_returns_request_id(client: Client):
    response = client.get("/health/live/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "civicflow"}
    uuid.UUID(response.headers["X-Request-ID"])


def test_valid_request_id_is_preserved(client: Client):
    request_id = str(uuid.uuid4())

    response = client.get("/health/live/", headers={"X-Request-ID": request_id})

    assert response.headers["X-Request-ID"] == request_id


def test_invalid_request_id_is_replaced(client: Client):
    response = client.get("/health/live/", headers={"X-Request-ID": "unsafe-value"})

    assert response.headers["X-Request-ID"] != "unsafe-value"
    uuid.UUID(response.headers["X-Request-ID"])


@pytest.mark.django_db
def test_readiness_checks_database(client: Client):
    response = client.get("/health/ready/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok"}}


@pytest.mark.django_db
def test_readiness_reports_database_failure(client: Client):
    with patch.object(connections["default"], "cursor", side_effect=OperationalError):
        response = client.get("/health/ready/")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unavailable",
        "checks": {"database": "failed"},
    }
