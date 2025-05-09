from json import loads as json_loads
from typing import Optional

from channels.db import aclose_old_connections

from camille.mattermost.client import Mattermost
from camille.models import MMChannel, MMMembership, MMTeam, MMUser


class MattermostAgent(Mattermost):
    def __init__(self, base_url: str, token: str):
        super().__init__(base_url, token)
        self.me: Optional[MMUser] = None

    async def connect(self):
        me_data = await self.get_me()
        self.me = (
            await MMUser.objects.aupdate_or_create(
                id=me_data.id,
                defaults={
                    "username": me_data.username,
                    "nickname": me_data.nickname,
                    "first_name": me_data.first_name,
                    "last_name": me_data.last_name,
                },
            )
        )[0]

        await super().connect()

    async def sync_db(self):
        for user_data in await self.get_users():
            await MMUser.objects.aupdate_or_create(
                id=user_data.id,
                defaults={
                    "username": user_data.username,
                    "nickname": user_data.nickname,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                },
            )

        for team_data in await self.get_teams(self.me.id):
            await MMTeam.objects.aupdate_or_create(
                id=team_data.id,
                defaults={
                    "name": team_data.name,
                    "display_name": team_data.display_name,
                },
            )
            for channel_data in await self.get_channels_for_user(
                self.me.id, team_data.id
            ):
                await MMChannel.objects.aupdate_or_create(
                    id=channel_data.id,
                    defaults={
                        "team_id": team_data.id,
                        "type": channel_data.type,
                        "name": channel_data.name,
                        "display_name": channel_data.display_name,
                        "header": channel_data.header,
                        "purpose": channel_data.purpose,
                    },
                )
                for member_data in await self.get_channel_members(channel_data.id):
                    await MMMembership.objects.aupdate_or_create(
                        channel_id=channel_data.id,
                        user_id=member_data.user_id,
                    )

    async def on_event(self, kind: str, data, broadcast, seq):
        await aclose_old_connections()
        await super().on_event(kind, data, broadcast, seq)

    async def on_hello(self, data, broadcast, seq):
        await self.sync_db()

    async def on_posted(self, data, broadcast, seq):
        post = json_loads(data["post"])
        channel = await MMChannel.get(id=post["channel_id"])
