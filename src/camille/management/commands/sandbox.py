import logging
from asyncio import run

from django.core.management.base import BaseCommand

from camille.models import MattermostServer, MattermostTeam
from mattermost import MattermostClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "sandbox command"

    async def async_handle(self):
        mm_server = await MattermostServer.objects.afirst()
        if mm_server is None:
            logger.warning("No MattermostServer found in database.")
            return

        mm_team = await MattermostTeam.objects.filter(server=mm_server).afirst()
        if mm_team is None:
            logger.warning("No MattermostTeam found in database.")
            return

        async with MattermostClient(
            base_url=mm_server.url,
            token=mm_server.token,
        ) as mm:
            pass

    def handle(self, *args, **options):
        run(self.async_handle())
