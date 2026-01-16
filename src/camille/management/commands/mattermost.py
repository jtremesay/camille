from asyncio import run
from logging import getLogger

from django.core.management.base import BaseCommand, CommandParser

from camille.mattermost import MattermostAgent
from camille.models import MattermostServer

logger = getLogger(__name__)


class Command(BaseCommand):
    help = "Mattermost agent"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "server_id", type=int, help="ID of the Mattermost server to connect to"
        )

        return super().add_arguments(parser)

    async def async_handle(self, server_id: int) -> None:
        try:
            mm_server = await MattermostServer.objects.aget(id=server_id)
        except MattermostServer.DoesNotExist:
            logger.error("No Mattermost server found with ID %d.", server_id)
            return

        async with MattermostAgent(mm_server=mm_server) as agent:
            await agent.run()

    def handle(self, *args, **options):
        run(self.async_handle(options["server_id"]))
