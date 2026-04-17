import logging
from asyncio import run

from django.core.management.base import BaseCommand

from camille.mattermost import Mattermost

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Mattermost agent"

    def handle(self, *args, **options):
        run(self.ahandle(*args, **options))

    async def ahandle(self, *args, **options):
        async with Mattermost() as mm:
            await mm.run()
