from django.core.management.base import BaseCommand

from laura.xmpp import XMPPBot


class Command(BaseCommand):
    help = "laura"

    def add_arguments(self, parser): ...

    def handle(self, *args, **options):
        bot = XMPPBot()
        bot.connect()
        bot.process()
