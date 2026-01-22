from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import KnownModelName, Model
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.bedrock import BedrockProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.mistral import MistralProvider

from camille.models import (
    BedrockCredentials,
    GoogleGLACredentials,
    MistralAICredentials,
    Profile,
)
from camille.schemas import ProfileSchema


@dataclass
class Deps:
    profile: Profile


def sp_user_context(ctx: RunContext[Deps]) -> str:
    profile_schema = ProfileSchema.from_orm(ctx.deps.profile)
    return f"You are talking with:\n```json\r\n{profile_schema.model_dump_json()}\n```"


def create_model_for_profile(
    profile: Profile, model: Model | str | KnownModelName
) -> Model | str:
    if not isinstance(model, Model):
        provider_name, model_name = model.split(":", 1)
        match provider_name:
            case "bedrock":
                creds = BedrockCredentials.objects.get(profile=profile)
                provider = BedrockProvider(
                    api_key=creds.api_key, region_name=creds.region
                )
                model = BedrockConverseModel(model_name=model_name, provider=provider)

            case "google-gla":
                creds = GoogleGLACredentials.objects.get(profile=profile)
                provider = GoogleProvider(api_key=creds.api_key)
                model = GoogleModel(model_name=model_name, provider=provider)

            case "mistral":
                creds = MistralAICredentials.objects.get(profile=profile)
                provider = MistralProvider(api_key=creds.api_key)
                model = MistralModel(model_name=model_name, provider=provider)

    return model


def create_agent_for_profile(profile: Profile) -> Agent[Deps]:
    agent = Agent(
        create_model_for_profile(
            profile, "bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
        ),
        deps_type=Deps,
    )
    agent.system_prompt(dynamic=True)(sp_user_context)

    return agent
