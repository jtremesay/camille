from pydantic_ai.models import Model
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.providers.bedrock import BedrockProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.mistral import MistralProvider

from camille.models import (
    AWSBedrockCredentials,
    GoogleGLACredentials,
    InferenceProvider,
    MistralAICredentials,
    MMUser,
)


async def create_bedrock_model_for_user(
    user: MMUser, model_name: str
) -> BedrockConverseModel:
    try:
        creds = await AWSBedrockCredentials.objects.aget(
            user=user, provider=InferenceProvider.AWS_BEDROCK
        )
    except AWSBedrockCredentials.DoesNotExist:
        raise ValueError("User does not have AWS Bedrock credentials configured.")

    provider = BedrockProvider(api_key=creds.bearer_token, region_name=creds.region)
    model = BedrockConverseModel(
        provider=provider,
        model_name=model_name,
    )
    return model


async def create_google_gla_model_for_user(
    user: MMUser, model_name: str
) -> GoogleModel:
    try:
        creds = await GoogleGLACredentials.objects.aget(
            user=user, provider=InferenceProvider.GOOGLE_GLA
        )
    except GoogleGLACredentials.DoesNotExist:
        raise ValueError("User does not have Google GLA credentials configured.")

    provider = GoogleProvider(api_key=creds.api_key)
    model = GoogleModel(
        provider=provider,
        model_name=model_name,
    )

    return model


async def create_mistral_model_for_user(user: MMUser, model_name: str) -> MistralModel:
    try:
        creds = await MistralAICredentials.objects.aget(
            user=user, provider=InferenceProvider.MISTRAL_AI
        )
    except MistralAICredentials.DoesNotExist:
        raise ValueError("User does not have Mistral AI credentials configured.")

    provider = MistralProvider(api_key=creds.api_key)
    model = MistralModel(
        provider=provider,
        model_name=model_name,
    )

    return model


async def create_model_for_user(user: MMUser) -> str | Model:
    model = user.model
    if not model:
        raise ValueError("User does not have a model configured.")

    provider, model_name = model.split(":", 1)
    match provider:
        case "bedrock":
            return await create_bedrock_model_for_user(user, model_name)

        case "google-gla":
            return await create_google_gla_model_for_user(user, model_name)

        case "mistral":
            return await create_mistral_model_for_user(user, model_name)

    return model
