import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """CivicFlow user identified by email instead of a username."""

    username = None
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.get_full_name() or self.email
