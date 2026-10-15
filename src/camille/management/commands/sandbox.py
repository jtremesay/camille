from argparse import ArgumentParser
from getpass import getuser
from typing import cast

from dbos import DBOS, DBOSConfig
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from pydantic_ai import Agent as PAIAgent

from camille.ai import create_pai_agent
from camille.models import Agent

dbos_config: DBOSConfig = {
    "name": "pydantic_dbos_agent",
    "system_database_url": f"sqlite:///{settings.BASE_DIR}/dbostest.sqlite3",
}
DBOS(config=dbos_config)


def run_flow(pai_agent: PAIAgent):
    @DBOS.workflow()
    def answer(question: str) -> str:
        result = pai_agent.run_sync(question)
        return result.output

    return answer


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

        prompt = "Quel fruit j'aime le plus ?"

        DBOS.launch()
        print(run_flow(pai_agent)(prompt))
