from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from camille.models import Agent

from .helpers import make_user


class SandboxCommandTests(TestCase):
    def test_reports_missing_default_agent(self):
        user = make_user()
        stderr = StringIO()

        call_command("sandbox", username=user.username, stderr=stderr)

        self.assertIn("No default agent found", stderr.getvalue())

    @mock.patch("camille.management.commands.sandbox.create_pai_agent")
    def test_runs_profile_default_agent(self, create_pai_agent):
        user = make_user()
        agent = Agent.objects.create(user=user)
        user.profile.default_agent = agent
        user.profile.save(update_fields=("default_agent",))
        create_pai_agent.return_value.run_sync.return_value.output = "A sheep"

        with mock.patch("builtins.print") as print_mock:
            call_command("sandbox", username=user.username)

        create_pai_agent.assert_called_once_with(agent)
        create_pai_agent.return_value.run_sync.assert_called_once_with(
            "dessine moi un mouton"
        )
        print_mock.assert_called_once_with("A sheep")

    @mock.patch("camille.management.commands.sandbox.create_pai_agent")
    def test_selects_agent_by_name(self, create_pai_agent):
        user = make_user()
        agent = Agent.objects.create(user=user, name="Artist")
        create_pai_agent.return_value.run_sync.return_value.output = "A sheep"

        with mock.patch("builtins.print"):
            call_command("sandbox", username=user.username, agent="Artist")

        create_pai_agent.assert_called_once_with(agent)

    def test_reports_unknown_named_agent(self):
        user = make_user()
        stderr = StringIO()

        call_command(
            "sandbox",
            username=user.username,
            agent="Missing",
            stderr=stderr,
        )

        self.assertIn("Agent named 'Missing' not found", stderr.getvalue())
