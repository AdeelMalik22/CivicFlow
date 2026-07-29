"""Local development settings."""

import os

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "local-development-only-secret-key")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
