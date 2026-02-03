from asyncio import run

from django.core.management.base import BaseCommand

from camille.mattermost import sync_mm_server
from camille.models import MattermostServer
from mattermost import Mattermost


class Command(BaseCommand):
    help = "Sync Mattermost teams and channels"

    async def ahandle(self, *args, **options):
        server = await MattermostServer.objects.aget()
        async with Mattermost(
            base_url=server.base_url,
            token=server.api_token,
        ) as mm:
            await sync_mm_server(server, mm)

    def handle(self, *args, **options):
        run(self.ahandle(*args, **options))
