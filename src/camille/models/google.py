from typing import cast

from django.core.exceptions import ValidationError
from encrypted_fields.fields import EncryptedCharField
from pydantic_ai.images.google import GoogleImageGenerationModel as PAIGoogleImageModel
from pydantic_ai.models.google import GoogleModel as PAIGoogleModel
from pydantic_ai.providers.google import GoogleProvider as PAIGoogleProvider

from .ai import AIImageModel, AIModel, AIProvider


class GoogleAIProvider(AIProvider):
    api_key = EncryptedCharField(max_length=255)

    def get_instance(self) -> PAIGoogleProvider:
        return PAIGoogleProvider(api_key=cast(str, self.api_key))


class GoogleAIModel(AIModel):
    def clean(self) -> None:
        if not isinstance(cast(AIProvider, self.provider), GoogleAIProvider):
            raise ValidationError(
                "The provider must be a Google AI provider for a Google AI model."
            )

        return super().clean()

    def get_instance(self) -> PAIGoogleModel:
        return PAIGoogleModel(
            model_name=cast(str, self.name),
            provider=cast(GoogleAIProvider, self.provider).get_instance(),
        )


class GoogleAIImageModel(AIImageModel):
    def clean(self) -> None:
        if not isinstance(cast(AIProvider, self.provider), GoogleAIProvider):
            raise ValidationError(
                "The provider must be a Google AI provider for a Google AI image model."
            )

        return super().clean()

    def get_instance(self) -> PAIGoogleImageModel:
        return PAIGoogleImageModel(
            model_name=cast(str, self.name),
            provider=cast(GoogleAIProvider, self.provider).get_instance(),
        )
