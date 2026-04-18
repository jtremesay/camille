import pytest
from unittest.mock import patch, AsyncMock

pytestmark = [pytest.mark.django_db(transaction=True)]

from camille.ai.models import (
    create_model_for_user,
    create_anthropic_model_for_user,
    create_bedrock_model_for_user,
    create_google_model_for_user,
    create_mistral_model_for_user,
    create_openrouter_model_for_user,
    NoCredentialsError,
)


class TestCreateModelForUser:
    async def test_unknown_provider_raises(self, user):
        with pytest.raises(ValueError, match="Unsupported model provider"):
            await create_model_for_user(user, "unknown:model-name")

    async def test_anthropic_dispatch(self, user, anthropic_credentials):
        model = await create_model_for_user(user, "anthropic:claude-3-opus")
        assert model is not None

    async def test_bedrock_dispatch(self, user, bedrock_credentials):
        model = await create_model_for_user(user, "bedrock:anthropic.claude-v2")
        assert model is not None

    async def test_google_dispatch(self, user, google_credentials):
        model = await create_model_for_user(user, "google-gla:gemini-pro")
        assert model is not None

    async def test_mistral_dispatch(self, user, mistral_credentials):
        model = await create_model_for_user(user, "mistral:mistral-large")
        assert model is not None

    async def test_openrouter_dispatch(self, user, openrouter_credentials):
        model = await create_model_for_user(user, "openrouter:meta-llama/llama-3")
        assert model is not None


class TestNoCredentials:
    async def test_anthropic_no_credentials(self, user):
        with pytest.raises(NoCredentialsError, match="Anthropic credentials"):
            await create_anthropic_model_for_user(user, "claude-3-opus")

    async def test_bedrock_no_credentials(self, user):
        with pytest.raises(NoCredentialsError, match="Bedrock credentials"):
            await create_bedrock_model_for_user(user, "anthropic.claude-v2")

    async def test_google_no_credentials(self, user):
        with pytest.raises(NoCredentialsError, match="Google GLA credentials"):
            await create_google_model_for_user(user, "gemini-pro")

    async def test_mistral_no_credentials(self, user):
        with pytest.raises(NoCredentialsError, match="Mistral credentials"):
            await create_mistral_model_for_user(user, "mistral-large")

    async def test_openrouter_no_credentials(self, user):
        with pytest.raises(NoCredentialsError, match="OpenRouter credentials"):
            await create_openrouter_model_for_user(user, "meta-llama/llama-3")


class TestModelStringParsing:
    async def test_colon_in_model_name(self, user, anthropic_credentials):
        """Model name with colon should work (split on first colon only)."""
        model = await create_model_for_user(user, "anthropic:claude-3:special")
        assert model is not None

    async def test_no_colon_raises(self, user):
        with pytest.raises(ValueError):
            await create_model_for_user(user, "no-colon-here")
