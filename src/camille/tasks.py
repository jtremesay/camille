from django_tasks import task

from camille.mattermost import sync_mm_server
from camille.models import MattermostServer
from mattermost import Mattermost


@task()
async def task_sync_mm_server(server_id: int):
    server = await MattermostServer.objects.aget(id=server_id)
    async with Mattermost(server.base_url, server.api_token) as mm:
        await sync_mm_server(server, mm)
