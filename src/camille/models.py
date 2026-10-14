from typing import cast
from uuid import uuid7

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from encrypted_fields.fields import EncryptedCharField
from polymorphic.models import PolymorphicModel
from pydantic_ai.models import Model as PAIModel
from pydantic_ai.models.google import GoogleModel as PAIGoogleModel
from pydantic_ai.models.openai import OpenAIChatModel as PAIOpenAIModel
from pydantic_ai.providers import Provider as PAIProvider
from pydantic_ai.providers.google import GoogleProvider as PAIGoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider as PAIOpenAIProvider


class Profile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        related_query_name="profile",
    )

    default_agent = models.ForeignKey(
        "Agent",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_profiles",
        related_query_name="default_for_profile",
    )

    default_model = models.ForeignKey(
        "AIModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_profiles",
        related_query_name="default_for_profile",
    )

    def clean(self):
        super().clean()

        if (
            self.default_agent is not None
            and cast(Agent, self.default_agent).user != self.user
        ):
            raise ValidationError("The default agent must belong to the same user.")

        if (
            self.default_model is not None
            and cast(AIModel, self.default_model).user != self.user
        ):
            raise ValidationError("The default model must belong to the same user.")

    def __str__(self) -> str:
        return cast(str, cast(User, self.user).username)


@receiver(post_save, sender=User)
def create_user_profile(
    sender: type[User], instance: User, created: bool, **kwargs
) -> None:
    """Create a Profile instance whenever a new User is created."""
    if not created:
        return

    Profile.objects.create(user=instance)


class Agent(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="agents",
        related_query_name="agent",
    )

    name = models.CharField(max_length=255, default="default")

    model = models.ForeignKey(
        "AIModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents",
        related_query_name="agent",
    )

    personality = models.ForeignKey(
        "AgentPersonality",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents",
        related_query_name="agent",
    )

    ddg_enabled = models.BooleanField(
        default=False, help_text="Enable DuckDuckGo search"
    )
    tavily_enabled = models.BooleanField(
        default=False, help_text="Enable Tavily integration"
    )
    webfetch_enabled = models.BooleanField(
        default=False, help_text="Enable fetching web content"
    )

    class Meta:
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return cast(str, self.name)

    def clean(self):
        super().clean()

        if (
            self.personality is not None
            and cast(AgentPersonality, self.personality).user != self.user
        ):
            raise ValidationError("The personality must belong to the same user.")

        if self.model is not None and cast(AIModel, self.model).user != self.user:
            raise ValidationError("The model must belong to the same user.")

    def get_model_instance(self) -> PAIModel:
        # Try to get the model assigned to the agent first
        if (model := cast(AIModel | None, self.model)) is not None:
            return model.get_instance()

        # If no model is assigned to the agent, try to get the default model from the user's profile
        if (
            default_model := cast(
                AIModel | None,
                cast(Profile, cast(User, self.user).profile).default_model,
            )
        ) is not None:
            return default_model.get_instance()

        # If no model is assigned to the agent and no default model is set in the user's profile, raise an error
        raise ValueError("The agent does not have a model assigned.")


class AgentPersonality(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="agent_personalities",
        related_query_name="agent_personality",
    )

    name = models.CharField(max_length=255, default="default")

    template = models.TextField(blank=True, default="You are {agent_name}")

    class Meta:
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return cast(str, self.name)


class AIProvider(PolymorphicModel):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ai_providers",
        related_query_name="ai_provider",
    )

    name = models.CharField(max_length=255, default="default")

    class Meta:
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return self.name

    def get_instance(self) -> PAIProvider:
        raise NotImplementedError("Subclasses must implement the get_instance method.")


class GoogleAIProvider(AIProvider):
    default_name = "google"

    api_key = EncryptedCharField(max_length=255)

    def get_instance(self) -> PAIGoogleProvider:
        return PAIGoogleProvider(api_key=cast(str, self.api_key))


class OpenAIAIProvider(AIProvider):
    default_name = "openai"

    api_key = EncryptedCharField(max_length=255)
    base_url = models.URLField(null=True, blank=True)

    def get_instance(self) -> PAIOpenAIProvider:
        return PAIOpenAIProvider(
            api_key=cast(str, self.api_key), base_url=cast(str | None, self.base_url)
        )


class AIModel(PolymorphicModel):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ai_models",
        related_query_name="ai_model",
    )

    provider = models.ForeignKey(
        AIProvider,
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


class TavilyApiKey(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tavily_api_keys",
        related_query_name="tavily_api_key",
    )

    name = models.CharField(max_length=255)

    key = models.CharField(max_length=255)

    class Meta:
        unique_together = ("user", "key")
