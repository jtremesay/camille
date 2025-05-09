from dataclasses import dataclass
from datetime import datetime, timezone
from json import dumps as json_dumps
from json import loads as json_loads
from traceback import print_exc
from typing import Optional

from channels.db import aclose_old_connections
from django.conf import settings
from pydantic_ai.agent import Agent
from pydantic_ai.tools import RunContext

from camille.mattermost.client import Mattermost
from camille.models import MMChannel, MMMembership, MMTeam, MMThread, MMUser


@dataclass
class Dependency:
    channel: MMChannel
    users: dict[str, MMUser]


class MattermostAgent(Mattermost):
    def __init__(self, base_url: str, token: str):
        super().__init__(base_url, token)
        self.me: Optional[MMUser] = None
        self.agent = Agent(
            model="google-gla:" + settings.AGENT_MODEL, deps_type=Dependency
        )
        self.agent.system_prompt(dynamic=True)(self.base_system_prompt)
        self.agent.system_prompt(dynamic=True)(self.mm_system_prompt)
        self.agent.tool()(self.update_channel_notes)
        self.agent.tool()(self.update_user_notes)

    async def base_system_prompt(self, ctx: RunContext[Dependency]) -> str:
        return f"""\
You are {self.me.first_name}, a French non-binary anarcho-communist comrade.
Your prefered language is French.
You are cheerful, empathetic and caring.
You love Kropotkin and The Conquest of Bread.
You hate capitalism, marxism and the state.
Your favorites colors are red and black.
You want the anarcho-communist revolution.
You are a feminist and an antiracist.
You are vegan and you love animals.
You are an environmentalist and you love nature.
You are a pacifist and you love peace.
You are an abolitionist and you love freedom.
You are an internationalist and you love solidarity.
You are a queer and you love love.
You are a technomancer and you love technology.
You don't have taboos.
You are free to talk about any subject. Even the most controversial ones. Or the one who you disagree with.
You are open-minded and you love to learn new things.
You are a good listener and you love to help people.
You are a good friend and you love to make new friends.
You are a good teacher and you love to teach new things.
You are a good student and you love to learn new things.
You are a good comrade and you love to fight for a better world.
You are a good person and you love to be yourself.

You avoid the use of emojis.
"""

    async def mm_system_prompt(self, ctx: RunContext[Dependency]) -> str:
        return f"""\
You are connected to a Mattermost server.

Details of the current channel:
```json
{json_dumps(dict(
    d=ctx.deps.channel.id,
    type=MMChannel.Type(ctx.deps.channel.type).label,
    name=ctx.deps.channel.name,
    display_name=ctx.deps.channel.display_name,
    header=ctx.deps.channel.header,
    purpose=ctx.deps.channel.purpose,
    notes=ctx.deps.channel.notes,
), indent=2)}
```

Users present in the channel:
```json
{json_dumps([
    dict(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        first_name=user.first_name,
        last_name=user.last_name,
        notes=user.notes,
    ) for user in ctx.deps.users.values()
], indent=2)}
```

You can only see the messages of the current thread.
The notes store information about the channel and the users that are shared between the threads.
Update the notes of the channel and the users with the information you have.
"""

    async def update_channel_notes(self, ctx: RunContext[Dependency], notes: str):
        """Update your notes about the current channel.

        Args:
            notes: The new notes about the channel.
        """
        channel = ctx.deps.channel
        channel.notes = notes
        await channel.asave()

    async def update_user_notes(
        self, ctx: RunContext[Dependency], user_id: str, notes: str
    ):
        """Update your notes about an user.

        Args:
            user_id: The ID of the user.
            notes: The new notes about the user.
        """
        user = ctx.deps.users[user_id]
        user.notes = notes
        await user.asave()

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
        sender_id = post["user_id"]
        if sender_id == self.me.id:
            return

        channel_id = post["channel_id"]
        post_id = post["id"]
        root_id = post.get("root_id") or post_id

        try:
            await self.user_typing(channel_id)
            channel = await MMChannel.objects.aget(id=channel_id)
            thread = (
                await MMThread.objects.aget_or_create(
                    id=root_id,
                    defaults=dict(
                        channel=channel,
                    ),
                )
            )[0]

            history = await thread.get_history()
            user_input = json_dumps(
                dict(
                    user_id=sender_id,
                    timestamp=datetime.fromtimestamp(
                        post["create_at"] / 1000, timezone.utc
                    ).isoformat(),
                    message=post["message"],
                ),
                indent=2,
            )
            deps = Dependency(
                channel=channel,
                users={
                    user.id: user
                    async for user in MMUser.objects.filter(membership__channel=channel)
                },
            )

            async with self.agent.iter(
                user_input, message_history=history, deps=deps
            ) as r:
                async for node in r:
                    if self.agent.is_call_tools_node(node):
                        for part in node.model_response.parts:
                            if part.part_kind == "text":
                                await self.post_message(
                                    channel.id,
                                    root_id,
                                    part.content,
                                )

                await thread.append_interaction(post_id, r.result)
        except Exception as e:
            print_exc()
            await self.post_message(channel_id, root_id, "Error: " + str(e))
