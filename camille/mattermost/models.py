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


async def create_model_for_user(user: MMUser) -> str | Model:
    if not user.model:
        raise ValueError("User does not have a model configured.")

    if user.model.startswith("bedrock:"):
        try:
            creds = await AWSBedrockCredentials.objects.aget(
                user=user, provider=InferenceProvider.AWS_BEDROCK
            )
        except AWSBedrockCredentials.DoesNotExist:
            raise ValueError("User does not have AWS Bedrock credentials configured.")

        provider = BedrockProvider(api_key=creds.bearer_token, region_name=creds.region)
        model = BedrockConverseModel(
            provider=provider,
            model_name=user.model.split("bedrock:")[1],
        )
        return model

    if user.model.startswith("google-gla:"):
        try:
            creds = await GoogleGLACredentials.objects.aget(
                user=user, provider=InferenceProvider.GOOGLE_GLA
            )
        except GoogleGLACredentials.DoesNotExist:
            raise ValueError("User does not have Google GLA credentials configured.")

        provider = GoogleProvider(api_key=creds.api_key)
        model = GoogleModel(
            provider=provider,
            model_name=user.model.split("google-gla:")[1],
        )

        return model

    if user.model.startswith("mistral:"):
        try:
            creds = await MistralAICredentials.objects.aget(
                user=user, provider=InferenceProvider.MISTRAL_AI
            )
        except MistralAICredentials.DoesNotExist:
            raise ValueError("User does not have Mistral AI credentials configured.")

        provider = MistralProvider(api_key=creds.api_key)
        model = MistralModel(
            provider=provider,
            model_name=user.model.split("mistral:")[1],
        )

        return model

    return user.model
