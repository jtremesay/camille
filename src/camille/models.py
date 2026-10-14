from uuid import uuid7

from django.db import models

# from encrypted_fields.fields import EncryptedCharField
from polymorphic.models import PolymorphicModel

# from pydantic_ai.models.google import GoogleModel
# from pydantic_ai.models.openai import OpenAIChatModel

# from pydantic_ai.providers.google import GoogleProvider
# from pydantic_ai.providers.openai import OpenAIProvider


class AIProvider(PolymorphicModel):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid7)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    # def get_provider_instance(self) -> Provider:
    #     raise NotImplementedError

    # def get_model_instance(self, model: AIModel) -> Model:
    #     raise NotImplementedError

    def save(self, *args, **kwargs):
        if type(self) is AIProvider:
            raise ValueError(
                "Cannot save an instance of the base AIProvider class directly."
            )

        super().save(*args, **kwargs)


# class AIProviderGoogle(AIProvider):
#     api_key = EncryptedCharField(max_length=255)

#     def get_provider_instance(self) -> GoogleProvider:
#         return GoogleProvider(api_key=self.api_key)

#     def get_model_instance(self, model: AIModel) -> Model:
#         return GoogleModel(model_name=model.name, provider=self.get_provider_instance())


# class AIProviderOpenAICompatible(AIProvider):
#     base_url = models.URLField(max_length=255)
#     api_key = EncryptedCharField(max_length=255, null=True, blank=True)

#     def get_provider_instance(self) -> OpenAIProvider:
#         return OpenAIProvider(base_url=self.base_url, api_key=self.api_key)

#     def get_model_instance(self, model: AIModel) -> OpenAIChatModel:
#         return OpenAIChatModel(
#             model_name=model.name, provider=self.get_provider_instance()
#         )


# class AIModel(models.Model):
#     provider = models.ForeignKey(AIProvider, on_delete=models.CASCADE)
#     name = models.CharField(max_length=255)

#     def get_model_instance(self) -> Model:
#         return self.provider.get_model_instance(self)


# class Agent(models.Model):
#     model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
#     personality = models.TextField()
