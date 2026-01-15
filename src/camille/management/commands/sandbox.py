from asyncio import run

from django.core.management.base import BaseCommand

from camille.mattermost import sync_db_all


class Command(BaseCommand):
    help = "sandbox command"

    async def async_handle(self):
        await sync_db_all()

    def handle(self, *args, **options):
        run(self.async_handle())
