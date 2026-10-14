from typing import cast
from uuid import uuid7

from django.core.exceptions import ValidationError
from django.db import models
from polymorphic.models import PolymorphicModel
from pydantic_ai.images import ImageGenerationModel as PAIImageModel
from pydantic_ai.models import Model as PAIModel
from pydantic_ai.providers import Provider as PAIProvider


class AIProvider(PolymorphicModel):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="ai_providers",
        related_query_name="ai_provider",
    )

    name = models.CharField(max_length=255, default="default")

    class Meta:
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return cast(str, self.name)

    def get_instance(self) -> PAIProvider:
        raise NotImplementedError("Subclasses must implement the get_instance method.")


class AIModel(PolymorphicModel):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="ai_models",
        related_query_name="ai_model",
    )

    provider = models.ForeignKey(
        "camille.AIProvider",
        on_delete=models.CASCADE,
        related_name="ai_models",
        related_query_name="ai_model",
    )
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("user", "provider", "name")

    def __str__(self) -> str:
        return f"{self.provider.name}:{cast(str, self.name)}"

    def clean(self) -> None:
        if cast(AIProvider, self.provider).user != self.user:
            raise ValidationError(
                "The provider must belong to the same user as the AI model."
            )

        return super().clean()

    def get_instance(self) -> PAIModel:
        raise NotImplementedError("Subclasses must implement the get_instance method.")


class AIImageModel(PolymorphicModel):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="ai_image_models",
        related_query_name="ai_image_model",
    )

    provider = models.ForeignKey(
        "camille.AIProvider",
        on_delete=models.CASCADE,
        related_name="ai_image_models",
        related_query_name="ai_image_model",
    )
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("user", "provider", "name")

    def __str__(self) -> str:
        return f"{self.provider.name}:{cast(str, self.name)}"

    def clean(self) -> None:
        if cast(AIProvider, self.provider).user != self.user:
            raise ValidationError(
                "The provider must belong to the same user as the AI model."
            )

        return super().clean()

    def get_instance(self) -> PAIImageModel:
        raise NotImplementedError("Subclasses must implement the get_instance method.")
