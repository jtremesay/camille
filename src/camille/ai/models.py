from pydantic_ai.models import Model
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


def create_model_for_profile(profile: Profile) -> Model | str:
    if not profile.model_name:
        raise ValueError("Profile does not have a default model name set.")

    provider_name, model_name = profile.model_name.split(":", 1)
    match provider_name:
        case "bedrock":
            creds = BedrockCredentials.objects.get(profile=profile)
            provider = BedrockProvider(api_key=creds.api_key, region_name=creds.region)
            model = BedrockConverseModel(model_name=model_name, provider=provider)

        case "google-gla":
            creds = GoogleGLACredentials.objects.get(profile=profile)
            provider = GoogleProvider(api_key=creds.api_key)
            model = GoogleModel(model_name=model_name, provider=provider)

        case "mistral":
            creds = MistralAICredentials.objects.get(profile=profile)
            provider = MistralProvider(api_key=creds.api_key)
            model = MistralModel(model_name=model_name, provider=provider)

        case _:
            model = model_name

    return model
