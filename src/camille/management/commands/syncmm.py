from django.core.management.base import BaseCommand

from camille.models import MattermostServer
from camille.tasks import task_sync_mm_server


class Command(BaseCommand):
    help = "Sync Mattermost teams and channels"

    def handle(self, *args, **options):
        server = MattermostServer.objects.get()
        a = task_sync_mm_server.enqueue(server_id=server.pk)
        print(a)
