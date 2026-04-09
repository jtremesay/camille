from asyncio import run

from django.core.management.base import BaseCommand

from camille.mattermost.agent import MattermostAgent


class Command(BaseCommand):
    help = "Mattermost agent"

    def handle(self, *args, **options):
        agent = MattermostAgent.create()
        run(agent.connect())
