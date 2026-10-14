from typing import cast
from uuid import uuid7

from django.contrib.auth.models import User
from django.db import models
from encrypted_fields.fields import EncryptedCharField


class ExaApiKey(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="exa_api_keys",
        related_query_name="exa_api_key",
    )

    name = models.CharField(max_length=255, default="default")
    key = EncryptedCharField(max_length=255)

    class Meta:
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return cast(str, self.name)
