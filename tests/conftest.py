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
from django.contrib.auth.models import User

from camille.models import (
    AgentConfig,
    AgentPersonality,
    AnthropicCredentials,
    AWSBedrockCredentials,
    GoogleGLACredentials,
    MattermostBinding,
    MistralCredentials,
    OpenRouterCredentials,
)


@pytest.fixture
def user(db):
    """Create a test user. The post_save signal auto-creates AgentConfig + default personality."""
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(username="otheruser", password="testpass123")


@pytest.fixture
def agent_config(user):
    return AgentConfig.objects.get(user=user)


@pytest.fixture
def personality(user):
    return AgentPersonality.objects.get(user=user, name="camille")


@pytest.fixture
def mattermost_binding(user):
    return MattermostBinding.objects.create(user=user, mm_id="mm_test_id_123")


@pytest.fixture
def anthropic_credentials(user):
    return AnthropicCredentials.objects.create(user=user, api_key="sk-ant-test-key")


@pytest.fixture
def bedrock_credentials(user):
    return AWSBedrockCredentials.objects.create(
        user=user, api_key="aws-test-key", region_name="us-east-1"
    )


@pytest.fixture
def google_credentials(user):
    return GoogleGLACredentials.objects.create(user=user, api_key="google-test-key")


@pytest.fixture
def mistral_credentials(user):
    return MistralCredentials.objects.create(user=user, api_key="mistral-test-key")


@pytest.fixture
def openrouter_credentials(user):
    return OpenRouterCredentials.objects.create(
        user=user, api_key="openrouter-test-key"
    )


@pytest.fixture
def logged_in_client(client, user):
    client.login(username="testuser", password="testpass123")
    return client
