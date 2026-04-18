import pytest
from unittest.mock import MagicMock

from camille.ai.deps import Deps, MattermostDeps


class TestDeps:
    def test_deps_creation(self):
        user = MagicMock()
        all_users = [MagicMock()]
        deps = Deps(agent_name="test-agent", current_user=user, all_users=all_users)

        assert deps.agent_name == "test-agent"
        assert deps.current_user == user
        assert deps.all_users == all_users


class TestMattermostDeps:
    def test_mattermost_deps_creation(self):
        user = MagicMock()
        all_users = [MagicMock()]
        deps = MattermostDeps(
            agent_name="test-agent",
            current_user=user,
            all_users=all_users,
            channel_name="test-channel",
        )

        assert deps.agent_name == "test-agent"
        assert deps.current_user == user
        assert deps.channel_name == "test-channel"
