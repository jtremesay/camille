import logging
from datetime import datetime, timezone

import logfire

from camille.models import MattermostServer, MattermostTeam
from mattermost import Mattermost, Team, User

TIMESTAMP_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

logger = logging.getLogger(__name__)


@logfire.instrument("mattermost_sync_db_all")
async def sync_db_all() -> None:
    async for mm_server in MattermostServer.objects.all():
        async with Mattermost(
            base_url=mm_server.url,
            token=mm_server.token,
        ) as mm:
            await sync_db_server(mm_server, mm)


@logfire.instrument("mattermost_sync_db_server {mm_server.name=}")
async def sync_db_server(mm_server: MattermostServer, mm: Mattermost) -> None:
    me = await mm.get_user("me")
    await sync_db_teams(mm_server, mm, me)


@logfire.instrument("mattermost_sync_db_teams {mm_server.name=} {me.username=}")
async def sync_db_teams(mm_server: MattermostServer, mm: Mattermost, me: User) -> None:
    teams = await mm.get_teams(me.id)
    for team in teams:
        await sync_db_team(mm_server, mm, team, me)


@logfire.instrument("mattermost_sync_db_team {team.name=}")
async def sync_db_team(
    mm_server: MattermostServer, mm: Mattermost, team: Team, me: User
) -> None:
    if team.delete_at > TIMESTAMP_EPOCH:
        logger.info("Deleting team '%s' from database.", team.name)
        await MattermostTeam.objects.filter(
            server=mm_server,
            team_id=team.id,
        ).adelete()
    else:
        logger.info("Syncing team '%s' to database.", team.name)
        mm_team, _ = await MattermostTeam.objects.aupdate_or_create(
            server=mm_server,
            team_id=team.id,
            defaults={
                "name": team.name,
                "display_name": team.display_name,
                "description": "",
                "create_at": team.create_at,
                "update_at": team.update_at,
            },
        )

        await sync_db_channels(mm_team, mm, me)


@logfire.instrument("mattermost_sync_db_channels {mm_team.name=}")
async def sync_db_channels(mm_team: MattermostTeam, mm: Mattermost, me: User) -> None:
    pass  # Placeholder for future implementation
