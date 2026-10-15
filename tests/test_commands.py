from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from camille.models import Agent

from .helpers import make_user


class CliCommandTestsMixin:
    """Shared expectations for the `sandbox` and `clai` commands.

    Both commands resolve an agent for a user, build a Pydantic AI agent and
    hand it over to the interactive CLI.
    """

    command: str

    @property
    def create_pai_agent_path(self) -> str:
        return f"camille.management.commands.{self.command}.create_pai_agent"

    def test_reports_missing_default_agent(self):
        user = make_user()
        stderr = StringIO()

        call_command(self.command, username=user.username, stderr=stderr)

        self.assertIn("No default agent found", stderr.getvalue())

    def test_reports_unknown_named_agent(self):
        user = make_user()
        stderr = StringIO()

        call_command(
            self.command,
            username=user.username,
            agent="Missing",
            stderr=stderr,
        )

        self.assertIn("Agent named 'Missing' not found", stderr.getvalue())

    def test_runs_profile_default_agent(self):
        user = make_user()
        agent = Agent.objects.create(user=user)
        user.profile.default_agent = agent
        user.profile.save(update_fields=("default_agent",))

        with mock.patch(self.create_pai_agent_path) as create_pai_agent:
            call_command(self.command, username=user.username)

        create_pai_agent.assert_called_once_with(agent, planning_session_id="sandbox")

    def test_selects_agent_by_name(self):
        user = make_user()
        agent = Agent.objects.create(user=user, name="Artist")
        Agent.objects.create(user=user, name="Writer")

        with mock.patch(self.create_pai_agent_path) as create_pai_agent:
            call_command(self.command, username=user.username, agent="Artist")

        create_pai_agent.assert_called_once_with(agent, planning_session_id="sandbox")

    def test_ignores_agents_owned_by_another_user(self):
        user = make_user()
        Agent.objects.create(user=make_user("bob"), name="Artist")
        stderr = StringIO()

        with mock.patch(self.create_pai_agent_path) as create_pai_agent:
            call_command(
                self.command,
                username=user.username,
                agent="Artist",
                stderr=stderr,
            )

        self.assertIn("Agent named 'Artist' not found", stderr.getvalue())
        create_pai_agent.assert_not_called()

    def test_reports_unknown_user(self):
        with self.assertRaises(User.DoesNotExist):
            call_command(self.command, username="nobody")


class SandboxCommandTests(CliCommandTestsMixin, TestCase):
    command = "sandbox"


class ClaiCommandTests(CliCommandTestsMixin, TestCase):
    command = "clai"

    def test_hands_the_agent_over_to_the_interactive_cli(self):
        user = make_user()
        agent = Agent.objects.create(user=user)
        user.profile.default_agent = agent
        user.profile.save(update_fields=("default_agent",))

        with mock.patch(self.create_pai_agent_path) as create_pai_agent:
            call_command(self.command, username=user.username)

        create_pai_agent.return_value.to_cli_sync.assert_called_once_with()
