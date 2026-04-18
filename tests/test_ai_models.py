import pytest

from camille.ai.models import (
    NoCredentialsError,
    create_anthropic_model_for_user,
    create_bedrock_model_for_user,
    create_google_model_for_user,
    create_mistral_model_for_user,
    create_openrouter_model_for_user,
    create_model_for_user,
)


@pytest.mark.django_db
class TestCreateAnthropicModel:
    @pytest.mark.asyncio
    async def test_no_credentials(self, user):
        with pytest.raises(
            NoCredentialsError, match="does not have Anthropic credentials"
        ):
            await create_anthropic_model_for_user(user, "claude-3-5-sonnet")


@pytest.mark.django_db
class TestCreateBedrockModel:
    @pytest.mark.asyncio
    async def test_no_credentials(self, user):
        with pytest.raises(
            NoCredentialsError, match="does not have Bedrock credentials"
        ):
            await create_bedrock_model_for_user(user, "model")


@pytest.mark.django_db
class TestCreateGoogleModel:
    @pytest.mark.asyncio
    async def test_no_credentials(self, user):
        with pytest.raises(
            NoCredentialsError, match="does not have Google GLA credentials"
        ):
            await create_google_model_for_user(user, "gemini")


@pytest.mark.django_db
class TestCreateMistralModel:
    @pytest.mark.asyncio
    async def test_no_credentials(self, user):
        with pytest.raises(
            NoCredentialsError, match="does not have Mistral credentials"
        ):
            await create_mistral_model_for_user(user, "mistral")


@pytest.mark.django_db
class TestCreateOpenRouterModel:
    @pytest.mark.asyncio
    async def test_no_credentials(self, user):
        with pytest.raises(
            NoCredentialsError, match="does not have OpenRouter credentials"
        ):
            await create_openrouter_model_for_user(user, "model")


@pytest.mark.django_db
class TestCreateModelForUser:
    @pytest.mark.asyncio
    async def test_invalid_provider(self, user):
        with pytest.raises(ValueError, match="Unsupported model provider"):
            await create_model_for_user(user, "unknown:model")
