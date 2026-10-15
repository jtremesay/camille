from argparse import ArgumentParser
from getpass import getuser
from typing import cast

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
                agent = cast(Agent, user.agents.get(name=agent_name))
            except Agent.DoesNotExist:
                self.stderr.write(f"Agent named '{agent_name}' not found for the user.")
                return
        elif (
            default_agent := cast(Agent | None, user.profile.default_agent)
        ) is not None:
            agent = default_agent
        else:
            self.stderr.write("No default agent found for the user.")
            return

        pai_agent = create_pai_agent(agent, planning_session_id="sandbox")
        pai_agent.to_cli_sync()

        return
        r = pai_agent.run_sync(
            # "Research the history of TLS and write a one-paragraph summary."
            "Renseigne toi sur comment établir la révolution communiste mondiale puis un plan en 5 étapes l'établir. Délègue chaque étape à un mignon. Execute les en parallèle. Ceci est un test pous évaluer ta capacité à planifier un plan, investiguer un sujet et déléguer des tâches. Les taches devront être dummy."
        )
        print(r.output)
