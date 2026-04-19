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

import pytest
from django.conf import settings
from django.contrib.auth.models import User

from camille.models import (
    AgentConfig,
    AgentPersonality,
    MattermostBinding,
    MattermostConversation,
    MattermostConversationRun,
)
from pydantic_ai.messages import ModelMessagesTypeAdapter


class TestPostSaveSignal:
    def test_user_creation_creates_agent_config(self, user):
        assert AgentConfig.objects.filter(user=user).exists()

    def test_user_creation_creates_default_personality(self, user):
        personality = AgentPersonality.objects.get(user=user, name="camille")
        assert personality.description == "The default personality."
        assert personality.prompt_template == settings.DEFAULT_PROMPT_TEMPLATE

    def test_agent_config_linked_to_default_personality(self, user):
        config = AgentConfig.objects.get(user=user)
        assert config.personality is not None
        assert config.personality.name == "camille"
        assert config.personality.user == user


class TestAgentConfigClean:
    def test_clean_valid_personality(self, user, agent_config, personality):
        agent_config.personality = personality
        agent_config.clean()  # Should not raise

    def test_clean_other_users_personality_raises(self, user, agent_config, other_user):
        other_personality = AgentPersonality.objects.get(user=other_user)
        agent_config.personality = other_personality
        with pytest.raises(
            ValueError, match="Personality must belong to the same user"
        ):
            agent_config.clean()

    def test_clean_no_personality(self, agent_config):
        agent_config.personality = None
        agent_config.clean()  # Should not raise


class TestMattermostBinding:
    def test_str(self, mattermost_binding):
        assert str(mattermost_binding) == "testuser"

    def test_unique_mm_id(self, mattermost_binding, other_user):
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            MattermostBinding.objects.create(user=other_user, mm_id="mm_test_id_123")


class TestAgentPersonality:
    def test_str(self, personality):
        assert str(personality) == "camille"

    def test_unique_together(self, user):
        with pytest.raises(Exception):  # IntegrityError
            AgentPersonality.objects.create(
                user=user,
                name="camille",
                prompt_template="duplicate",
            )

    def test_create_second_personality(self, user):
        p = AgentPersonality.objects.create(
            user=user, name="other", prompt_template="You are other."
        )
        assert p.name == "other"


class TestMattermostConversation:
    @pytest.mark.django_db(transaction=True)
    async def test_amessages_empty(self):
        conv = await MattermostConversation.objects.acreate(
            root_id="root123", channel_id="chan123"
        )
        messages = await conv.amessages()
        assert messages == []

    @pytest.mark.django_db(transaction=True)
    async def test_amessages_with_runs(self, user):
        conv = await MattermostConversation.objects.acreate(
            root_id="root456", channel_id="chan456"
        )
        # Create a run with a simple user message
        from pydantic_ai.messages import ModelRequest, UserPromptPart

        test_messages = [ModelRequest(parts=[UserPromptPart(content="hello")])]
        json_bytes = ModelMessagesTypeAdapter.dump_json(test_messages)
        await MattermostConversationRun.objects.acreate(
            conversation=conv, user=user, messages_json=json_bytes
        )
        messages = await conv.amessages()
        assert len(messages) == 1


class TestMattermostConversationRun:
    def test_messages_deserialization(self, user):
        from pydantic_ai.messages import ModelRequest, UserPromptPart

        test_messages = [ModelRequest(parts=[UserPromptPart(content="test")])]
        json_bytes = ModelMessagesTypeAdapter.dump_json(test_messages)

        conv = MattermostConversation.objects.create(
            root_id="root789", channel_id="chan789"
        )
        run = MattermostConversationRun.objects.create(
            conversation=conv, user=user, messages_json=json_bytes
        )
        result = run.messages()
        assert len(result) == 1
