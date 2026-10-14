from typing import TYPE_CHECKING, cast
from uuid import uuid7

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from pydantic_ai.models import Model as PAIModel

if TYPE_CHECKING:
    from .ai import AIImageModel, AIModel
    from .exa import ExaApiKey
    from .profile import Profile
    from .tavily import TavilyApiKey


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
    exa_enabled = models.BooleanField(default=False, help_text="Enable Exa search")
    exa_api_key = models.ForeignKey(
        "ExaApiKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents",
        related_query_name="agent",
    )
    tavily_enabled = models.BooleanField(
        default=False, help_text="Enable Tavily integration"
    )
    tavily_api_key = models.ForeignKey(
        "TavilyApiKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agents",
        related_query_name="agent",
    )
    webfetch_enabled = models.BooleanField(
        default=False, help_text="Enable fetching web content"
    )
    imgen_enabled = models.BooleanField(
        default=False, help_text="Enable image generation"
    )
    imgen_model = models.ForeignKey(
        "AIImageModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imgen_agents",
        related_query_name="imgen_agent",
    )

    class Meta:
        unique_together = ("user", "name")

    def __str__(self) -> str:
        return cast(str, self.name)

    def clean(self):
        super().clean()

        if (model := self.model) is not None and cast(
            "AIModel", model
        ).user != self.user:
            raise ValidationError("The model must belong to the same user.")

        if (personality := self.personality) is not None and cast(
            "AgentPersonality", personality
        ).user != self.user:
            raise ValidationError("The personality must belong to the same user.")

        if (exa_api_key := self.exa_api_key) is not None and cast(
            "ExaApiKey", exa_api_key
        ).user != self.user:
            raise ValidationError("The Exa API key must belong to the same user.")

        if (tavily_api_key := self.tavily_api_key) is not None and cast(
            "TavilyApiKey", tavily_api_key
        ).user != self.user:
            raise ValidationError("The Tavily API key must belong to the same user.")

        if (imgen_model := self.imgen_model) is not None and cast(
            "AIImageModel", imgen_model
        ).user != self.user:
            raise ValidationError(
                "The image generation model must belong to the same user."
            )

    def get_model_instance(self) -> PAIModel:
        # Try to get the model assigned to the agent first
        if (model := cast("AIModel | None", self.model)) is not None:
            return model.get_instance()

        # If no model is assigned to the agent, try to get the default model from the user's profile
        if (
            default_model := cast(
                "AIModel | None",
                cast("Profile", cast(User, self.user).profile).default_model,
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
