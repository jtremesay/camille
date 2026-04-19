# Camille - An AI assistant
# Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from django.contrib.auth.models import User
from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.mistral import MistralModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.bedrock import BedrockProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.mistral import MistralProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider

from camille.models import (
    AnthropicCredentials,
    AWSBedrockCredentials,
    GoogleGLACredentials,
    MistralCredentials,
    OpenRouterCredentials,
)


class NoCredentialsError(ValueError):
    pass


async def create_anthropic_model_for_user(user: User, model_name: str) -> Model:
    try:
        credentials = await AnthropicCredentials.objects.aget(user=user)
    except AnthropicCredentials.DoesNotExist:
        raise NoCredentialsError(
            f"User {user.username} does not have Anthropic credentials"
        )

    return AnthropicModel(
        model_name,
        provider=AnthropicProvider(api_key=credentials.api_key),
    )


async def create_bedrock_model_for_user(user: User, model_name: str) -> Model:
    try:
        credentials = await AWSBedrockCredentials.objects.aget(user=user)
    except AWSBedrockCredentials.DoesNotExist:
        raise NoCredentialsError(
            f"User {user.username} does not have Bedrock credentials"
        )

    return BedrockConverseModel(
        model_name,
        provider=BedrockProvider(
            api_key=credentials.api_key, region_name=credentials.region_name
        ),
    )


async def create_google_model_for_user(user: User, model_name: str) -> Model:
    try:
        credentials = await GoogleGLACredentials.objects.aget(user=user)
    except GoogleGLACredentials.DoesNotExist:
        raise NoCredentialsError(
            f"User {user.username} does not have Google GLA credentials"
        )

    return GoogleModel(
        model_name,
        provider=GoogleProvider(api_key=credentials.api_key),
    )


async def create_mistral_model_for_user(user: User, model_name: str) -> Model:
    try:
        credentials = await MistralCredentials.objects.aget(user=user)
    except MistralCredentials.DoesNotExist:
        raise NoCredentialsError(
            f"User {user.username} does not have Mistral credentials"
        )

    return MistralModel(
        model_name,
        provider=MistralProvider(api_key=credentials.api_key),
    )


async def create_openrouter_model_for_user(user: User, model_name: str) -> Model:
    try:
        credentials = await OpenRouterCredentials.objects.aget(user=user)
    except OpenRouterCredentials.DoesNotExist:
        raise NoCredentialsError(
            f"User {user.username} does not have OpenRouter credentials"
        )

    return OpenRouterModel(
        model_name,
        provider=OpenRouterProvider(api_key=credentials.api_key),
    )


async def create_model_for_user(user: User, model: str) -> Model:
    model_provider, model_name = model.split(":", 1)

    match model_provider:
        case "anthropic":
            return await create_anthropic_model_for_user(user, model_name)

        case "bedrock":
            return await create_bedrock_model_for_user(user, model_name)

        case "google-gla":
            return await create_google_model_for_user(user, model_name)

        case "mistral":
            return await create_mistral_model_for_user(user, model_name)

        case "openrouter":
            return await create_openrouter_model_for_user(user, model_name)

        case _:
            raise ValueError(f"Unsupported model provider: {model_provider}")
