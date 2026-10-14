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
            help="Slug of the agent to run the sandbox for. Defaults to the user's default agent.",
        )

    def handle(
        self,
        *args,
        **options,
    ):
        user = User.objects.get(username=options["username"])

        if (agent_slug := options["agent"]) is not None:
            try:
                agent = user.agents.get(slug=agent_slug)
            except Agent.DoesNotExist:
                self.stderr.write(
                    f"Agent with slug '{agent_slug}' not found for the user."
                )
                return
        elif user.profile.default_agent is not None:
            agent = user.profile.default_agent
        else:
            self.stderr.write("No default agent found for the user.")
            return

        pai_agent = create_pai_agent(agent)

        r = pai_agent.run_sync("quel est le box office de l'année 2026 ?")
        print(r.output)
