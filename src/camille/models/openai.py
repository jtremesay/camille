from typing import cast

from django.core.exceptions import ValidationError
from django.db import models
from encrypted_fields.fields import EncryptedCharField
from pydantic_ai.images.openai import OpenAIImageGenerationModel as PAIOpenAIImageModel
from pydantic_ai.models.openai import OpenAIChatModel as PAIOpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider as PAIOpenAIProvider

from .ai import AIImageModel, AIModel, AIProvider


class OpenAIAIProvider(AIProvider):
    api_key = EncryptedCharField(max_length=255)
    base_url = models.URLField(null=True, blank=True)

    def get_instance(self) -> PAIOpenAIProvider:
        return PAIOpenAIProvider(
            api_key=cast(str, self.api_key), base_url=cast(str | None, self.base_url)
        )


class OpenAIModel(AIModel):
    def clean(self) -> None:
        if not isinstance(cast(AIProvider, self.provider), OpenAIAIProvider):
            raise ValidationError(
                "The provider must be an OpenAI provider for an OpenAI model."
            )

        return super().clean()

    def get_instance(self) -> PAIOpenAIModel:
        return PAIOpenAIModel(
            model_name=cast(str, self.name),
            provider=cast(OpenAIAIProvider, self.provider).get_instance(),
        )


class OpenAIImageModel(AIImageModel):
    def clean(self) -> None:
        if not isinstance(cast(AIProvider, self.provider), OpenAIAIProvider):
            raise ValidationError(
                "The provider must be an OpenAI provider for an OpenAI image model."
            )

        return super().clean()

    def get_instance(self) -> PAIOpenAIImageModel:
        return PAIOpenAIImageModel(
            model_name=cast(str, self.name),
            provider=cast(OpenAIAIProvider, self.provider).get_instance(),
        )
