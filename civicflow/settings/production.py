"""Production settings that fail closed when configuration is incomplete."""

import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def required_environment_value(name: str) -> str:
    """Return a required environment value or stop startup with a safe error."""
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f"The {name} environment variable is required.")
    return value


SECRET_KEY = required_environment_value("DJANGO_SECRET_KEY")
DATABASES = {
    "default": dj_database_url.parse(
        required_environment_value("DATABASE_URL"),
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=os.getenv("DATABASE_SSL_REQUIRED", "true").lower() == "true",
    )
}

ALLOWED_HOSTS = [
    host.strip()
    for host in required_environment_value("DJANGO_ALLOWED_HOSTS").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

REDIS_URL = required_environment_value("REDIS_URL")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "true").lower() == "true"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

LOGGING["root"]["level"] = os.getenv("DJANGO_LOG_LEVEL", "INFO")  # noqa: F405
