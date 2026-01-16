import logging
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Optional

import logfire

from camille.models import (
    MattermostChannel,
    MattermostChannelMember,
    MattermostServer,
    MattermostTeam,
    MattermostUser,
)
from mattermost import Channel, ChannelMember, Mattermost, Team, User

TIMESTAMP_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

logger = logging.getLogger(__name__)


@logfire.instrument(
    "mattermost_get_sync_user_from_data {mm_server.name=} {user_data.username=}"
)
async def get_sync_user_from_data(
    mm_server: MattermostServer, user_data: User
) -> Optional[MattermostUser]:
    if user_data.delete_at > TIMESTAMP_EPOCH:
        logger.info("Deleting user '%s' from database.", user_data.username)
        await MattermostUser.objects.filter(
            server=mm_server,
            user_id=user_data.id,
        ).adelete()
        return None

    mm_user, _ = await MattermostUser.objects.aupdate_or_create(
        server=mm_server,
        user_id=user_data.id,
        defaults={
            "username": user_data.username,
            "nickname": user_data.nickname,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "create_at": user_data.create_at,
            "update_at": user_data.update_at,
        },
    )

    return mm_user


@logfire.instrument("mattermost_get_sync_user {mm_server.name=} {user_id=}")
async def get_sync_user(
    mm: Mattermost, mm_server: MattermostServer, user_id: str
) -> Optional[MattermostUser]:
    user_data = await mm.get_user(user_id)
    return await get_sync_user_from_data(mm_server, user_data)


@logfire.instrument("mattermost_get_sync_me {mm_server.name=}")
async def get_sync_me(
    mm: Mattermost, mm_server: MattermostServer
) -> Optional[MattermostUser]:
    return await get_sync_user(mm, mm_server, "me")


@logfire.instrument("mattermost_get_sync_users {mm_server.name=}")
async def get_sync_users(
    mm: Mattermost, mm_server: MattermostServer
) -> dict[str, MattermostUser]:
    mm_users = {}
    for user_data in await mm.get_users():
        mm_user = await get_sync_user_from_data(mm_server, user_data)
        if mm_user is not None:
            mm_users[user_data.id] = mm_user

    return mm_users


@logfire.instrument(
    "mattermost_get_sync_team_from_data {mm_server.name=} {team_data.name=}"
)
async def get_sync_team_from_data(
    mm_server: MattermostServer, team_data: Team
) -> Optional[MattermostTeam]:
    if team_data.delete_at > TIMESTAMP_EPOCH:
        logger.info("Deleting team '%s' from database.", team_data.name)
        await MattermostTeam.objects.filter(
            server=mm_server,
            team_id=team_data.id,
        ).adelete()
        return None

    mm_team, _ = await MattermostTeam.objects.aupdate_or_create(
        server=mm_server,
        team_id=team_data.id,
        defaults={
            "name": team_data.name,
            "display_name": team_data.display_name,
            "description": "",
            "create_at": team_data.create_at,
            "update_at": team_data.update_at,
        },
    )

    return mm_team


@logfire.instrument("mattermost_get_sync_teams {mm_server.name=}")
async def get_sync_teams(
    mm: Mattermost, mm_server: MattermostServer
) -> dict[str, MattermostTeam]:
    mm_teams = {}
    for team_data in await mm.get_teams("me"):
        mm_team = await get_sync_team_from_data(mm_server, team_data)
        if mm_team is not None:
            mm_teams[team_data.id] = mm_team

    return mm_teams


async def get_sync_channel_from_data(
    mm_team: MattermostTeam,
    channel_data: Channel,
) -> Optional[MattermostChannel]:
    if channel_data.delete_at > TIMESTAMP_EPOCH:
        logger.info("Deleting channel '%s' from database.", channel_data.name)
        await MattermostChannel.objects.filter(
            team=mm_team,
            channel_id=channel_data.id,
        ).adelete()
        return None

    mm_channel, _ = await MattermostChannel.objects.aupdate_or_create(
        team=mm_team,
        channel_id=channel_data.id,
        defaults={
            "name": channel_data.name,
            "display_name": channel_data.display_name,
            "header": channel_data.header,
            "purpose": channel_data.purpose,
            "last_post_at": channel_data.last_post_at,
            "create_at": channel_data.create_at,
            "update_at": channel_data.update_at,
        },
    )

    return mm_channel


@logfire.instrument("mattermost_get_sync_channels_for_team {mm_team.name=}")
async def get_sync_channels_for_team(
    mm: Mattermost, mm_team: MattermostTeam
) -> dict[str, MattermostChannel]:
    mm_channels = {}
    for channel_data in await mm.get_channels_for_user("me", mm_team.team_id):
        mm_channel = await get_sync_channel_from_data(mm_team, channel_data)
        if mm_channel is not None:
            mm_channels[channel_data.id] = mm_channel

    return mm_channels


@logfire.instrument("mattermost_get_sync_channels {mm_teams=}")
async def get_sync_channels(
    mm: Mattermost, mm_teams: Iterable[MattermostTeam]
) -> dict[str, MattermostChannel]:
    mm_channels = {}
    for mm_team in mm_teams:
        mm_channels.update(await get_sync_channels_for_team(mm, mm_team))

    return mm_channels


@logfire.instrument(
    "mattermost_get_sync_channel_member_from_data {mm_channel.name=} {channel_member_data.user_id=}"
)
async def get_sync_channel_member_from_data(
    mm_channel: MattermostChannel,
    channel_member_data: ChannelMember,
    mm_users: dict[str, MattermostUser],
) -> MattermostChannelMember:
    mm_membership, _ = await MattermostChannelMember.objects.aupdate_or_create(
        channel=mm_channel,
        user=mm_users[channel_member_data.user_id],
        defaults={},
    )
    return mm_membership


@logfire.instrument("mattermost_get_sync_channel_members {mm_channel.name=}")
async def get_sync_channel_members(
    mm: Mattermost,
    mm_channel: MattermostChannel,
    mm_users: dict[str, MattermostUser],
) -> list[MattermostChannelMember]:
    mm_memberships = []
    channel_members_data = await mm.get_channel_members(mm_channel.channel_id)

    for channel_member_data in channel_members_data:
        mm_memberships.append(
            await get_sync_channel_member_from_data(
                mm_channel,
                channel_member_data,
                mm_users,
            )
        )

    return mm_memberships


@logfire.instrument("mattermost_get_sync_channels_members")
async def get_sync_channels_members(
    mm: Mattermost,
    mm_users: dict[str, MattermostUser],
    mm_channels: dict[str, MattermostChannel],
) -> list[MattermostChannelMember]:
    mm_memberships = []
    for mm_channel in mm_channels.values():
        mm_memberships.extend(await get_sync_channel_members(mm, mm_channel, mm_users))

    return mm_memberships


@logfire.instrument("mattermost_sync_db_server {mm_server.name=}")
async def sync_db_server(
    mm: Mattermost, mm_server: MattermostServer
) -> Optional[
    tuple[
        MattermostUser,
        dict[str, MattermostUser],
        dict[str, MattermostTeam],
        dict[str, MattermostChannel],
        list[MattermostChannelMember],
    ]
]:
    mm_me = await get_sync_me(mm, mm_server)
    if mm_me is None:
        logger.warning(
            "Cannot sync server '%s' because the sync user could not be found.",
            mm_server.name,
        )
        return

    mm_users = await get_sync_users(mm, mm_server)
    mm_teams = await get_sync_teams(mm, mm_server)
    mm_channels = await get_sync_channels(mm, mm_teams.values())
    mm_channels_members = await get_sync_channels_members(mm, mm_users, mm_channels)

    return mm_me, mm_users, mm_teams, mm_channels, mm_channels_members


@logfire.instrument("mattermost_sync_db_all")
async def sync_db_all() -> dict[
    MattermostServer,
    tuple[
        MattermostUser,
        dict[str, MattermostUser],
        dict[str, MattermostTeam],
        dict[str, MattermostChannel],
        list[MattermostChannelMember],
    ],
]:
    results = {}
    async for mm_server in MattermostServer.objects.all():
        async with Mattermost(
            base_url=mm_server.url,
            token=mm_server.token,
        ) as mm:
            result = await sync_db_server(mm, mm_server)
            if result is not None:
                results[mm_server] = result

    return results


class MattermostAgent:
    def __init__(self, mm_server: MattermostServer) -> None:
        self.mm_server = mm_server
        self.mm: Mattermost = Mattermost(
            base_url=mm_server.url,
            token=mm_server.token,
        )
        self.mm_me: Optional[MattermostUser] = None
        self.mm_users: dict[str, MattermostUser] = {}
        self.mm_teams: dict[str, MattermostTeam] = {}
        self.mm_channels: dict[str, MattermostChannel] = {}
        self.mm_channel_members: list[MattermostChannelMember] = []

    async def __aenter__(self) -> "MattermostAgent":
        await self.mm.__aenter__()

        res = await sync_db_server(self.mm, self.mm_server)
        if res is None:
            raise RuntimeError(
                f"Cannot sync server '{self.mm_server.name}' because the sync user could not be found."
            )

        (
            self.mm_me,
            self.mm_users,
            self.teams,
            self.channels,
            self.channel_members,
        ) = res

        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.mm.__aexit__(exc_type, exc, tb)

    async def run(self) -> None:
        pass
