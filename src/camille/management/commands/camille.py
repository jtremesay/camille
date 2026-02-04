from asyncio import run

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run camille"

    def handle(self, *args, **options):
        run(self.async_handle(*args, **options))

    async def async_handle(self, *args, **options):
        pass
