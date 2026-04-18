import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError

from camille.models import (
    AgentConfig,
    AgentPersonality,
    AnthropicCredentials,
    AWSBedrockCredentials,
    GoogleGLACredentials,
    MattermostBinding,
    MattermostConversation,
    MattermostConversationRun,
    MistralCredentials,
    OpenRouterCredentials,
)


@pytest.mark.django_db
class TestMattermostBinding:
    def test_create_binding(self, user):
        binding = MattermostBinding.objects.create(user=user, mm_id="mm123")
        assert binding.user == user
        assert binding.mm_id == "mm123"

    def test_unique_mm_id(self, user):
        MattermostBinding.objects.create(user=user, mm_id="mm123")
        with pytest.raises(IntegrityError):
            MattermostBinding.objects.create(user=user, mm_id="mm123")

    def test_str(self, user):
        binding = MattermostBinding.objects.create(user=user, mm_id="mm123")
        assert str(binding) == "testuser"


@pytest.mark.django_db
class TestAgentPersonality:
    def test_create_personality(self, user):
        personality = AgentPersonality.objects.create(
            user=user,
            name="test-bot",
            description="Test bot",
            prompt_template="You are {agent_name}",
        )
        assert personality.user == user
        assert personality.name == "test-bot"

    def test_unique_user_name(self, user):
        AgentPersonality.objects.create(
            user=user, name="test-bot", prompt_template="test"
        )
        with pytest.raises(IntegrityError):
            AgentPersonality.objects.create(
                user=user, name="test-bot", prompt_template="test"
            )

    def test_str(self, user):
        personality = AgentPersonality.objects.create(
            user=user, name="test-bot", prompt_template="test"
        )
        assert str(personality) == "test-bot"


@pytest.mark.django_db
class TestAgentConfig:
    def test_create_config_updates_existing(self, user):
        user.agent_config.model = "anthropic:claude-3-5-sonnet-20241022"
        user.agent_config.save()
        user.agent_config.refresh_from_db()
        assert user.agent_config.model == "anthropic:claude-3-5-sonnet-20241022"

    def test_clean_validates_personality_ownership(self, user):
        other_user = User.objects.create_user(username="other", password="pass")
        personality = AgentPersonality.objects.create(
            user=other_user, name="other-bot", prompt_template="test"
        )
        config = AgentConfig(user=user, model="test", personality=personality)
        with pytest.raises(ValueError, match="must belong to the same user"):
            config.clean()


@pytest.mark.django_db
class TestCredentialsModels:
    def test_anthropic_credentials(self, user):
        cred = AnthropicCredentials.objects.create(user=user, api_key="sk-test")
        assert cred.user == user
        assert cred.api_key == "sk-test"

    def test_aws_bedrock_credentials(self, user):
        cred = AWSBedrockCredentials.objects.create(
            user=user, api_key="key", region_name="us-east-1"
        )
        assert cred.user == user
        assert cred.region_name == "us-east-1"

    def test_google_gla_credentials(self, user):
        cred = GoogleGLACredentials.objects.create(user=user, api_key="google-key")
        assert cred.user == user

    def test_mistral_credentials(self, user):
        cred = MistralCredentials.objects.create(user=user, api_key="mistral-key")
        assert cred.user == user

    def test_openrouter_credentials(self, user):
        cred = OpenRouterCredentials.objects.create(user=user, api_key="router-key")
        assert cred.user == user


@pytest.mark.django_db
class TestMattermostConversation:
    def test_create_conversation(self):
        conv = MattermostConversation.objects.create(
            root_id="root123", channel_id="channel456"
        )
        assert conv.root_id == "root123"
        assert conv.channel_id == "channel456"

    def test_unique_root_id(self):
        MattermostConversation.objects.create(root_id="root123", channel_id="ch1")
        with pytest.raises(IntegrityError):
            MattermostConversation.objects.create(root_id="root123", channel_id="ch2")


@pytest.mark.django_db
class TestMattermostConversationRun:
    def test_create_run(self, user):
        conv = MattermostConversation.objects.create(
            root_id="root123", channel_id="channel456"
        )
        run = MattermostConversationRun.objects.create(
            conversation=conv, user=user, messages_json=b"[]"
        )
        assert run.conversation == conv
        assert run.user == user


@pytest.mark.django_db
class TestAgentConfigSignal:
    def test_create_config_on_user_creation(self, db):
        user = User.objects.create_user(username="newuser", password="pass")
        config = AgentConfig.objects.get(user=user)
        assert config.model == ""
        personality = config.personality
        assert personality.name == "camille"
        assert personality.user == user
