from argparse import ArgumentParser
from getpass import getuser

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from camille.ai import create_pai_agent
from camille.models import Agent


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--username",
            type=str,
            default=getuser(),
            help="Username of the user to run the sandbox for.",
        )
        parser.add_argument(
            "--agent",
            type=str,
            default=None,
            help="Name of the agent to run the sandbox for. Defaults to the user's default agent.",
        )

    def handle(
        self,
        *args,
        **options,
    ):
        user = User.objects.get(username=options["username"])

        if (agent_name := options["agent"]) is not None:
            try:
                agent = user.agents.get(name=agent_name)
            except Agent.DoesNotExist:
                self.stderr.write(f"Agent named '{agent_name}' not found for the user.")
                return
        elif user.profile.default_agent is not None:
            agent = user.profile.default_agent
        else:
            self.stderr.write("No default agent found for the user.")
            return

        pai_agent = create_pai_agent(agent)

        r = pai_agent.run_sync(
            "quels sont les blockbusters bollywoodiens de l'été 2026"
        )
        print(r.output)
