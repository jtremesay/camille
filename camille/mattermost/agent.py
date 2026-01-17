from dataclasses import dataclass
from datetime import datetime, timezone
from json import dumps as json_dumps
from json import loads as json_loads
from typing import Optional

import logfire
from channels.db import aclose_old_connections
from django.conf import settings
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.common_tools.tavily import tavily_search_tool

from camille.mattermost.client import Mattermost
from camille.mattermost.commands import handle_command
from camille.mattermost.models import create_model_for_user
from camille.mattermost.tools import mm_system_prompt, toolset
from camille.models import MMChannel, MMMembership, MMTeam, MMThread, MMUser
from camille.prompts import DARK_DIHYAI_PROMPT


@dataclass
class Dependency:
    channel: MMChannel
    users: dict[str, MMUser]


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
        if self.me is None:
            raise RuntimeError("Bot user is not initialized")

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

    @logfire.instrument("event {kind=}")
    async def on_event(self, kind: str, data, broadcast, seq):
        await aclose_old_connections()
        await super().on_event(kind, data, broadcast, seq)

    async def on_hello(self, data, broadcast, seq):
        await self.sync_db()

    async def on_posted(self, data, broadcast, seq):
        if self.me is None:
            raise RuntimeError("Bot user is not initialized")

        post = json_loads(data["post"])

        # Ignore posts sent by the bot itself
        sender_id = post["user_id"]
        if sender_id == self.me.id:
            return

        # Ignore messages that are not simple text posts
        if post["type"]:
            return

        channel_type = data["channel_type"]
        channel_id = post["channel_id"]
        post_id = post["id"]
        root_id = post.get("root_id") or post_id
        message = post["message"]

        try:
            # Handle commands starting with "!/"
            if message.startswith("!/"):
                command_line = message[2:].strip()
                await handle_command(
                    self,
                    command_line,
                    channel_id,
                    root_id,
                    sender_id,
                )
                return

            if mentions_data := data.get("mentions"):
                mentions = set(json_loads(mentions_data))
            else:
                mentions = set()

            # Respond only if DM or if mentioned in a channel
            if not (channel_type == "D" or self.me.id in mentions):
                return

            mm_user = await MMUser.objects.aget(id=sender_id)
            if not mm_user.model:
                await self.post_message(
                    channel_id=channel_id,
                    root_id=root_id,
                    message="No model configured for your user. Please set up your model first.",
                )
                return

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
            user_input = []
            for file in post["metadata"].get("files", []):
                content = await self.get_file(file["id"])
                user_input.extend(
                    (
                        f"The file {file['name']} is attached.",
                        BinaryContent(data=content, media_type=file["mime_type"]),
                    )
                )
            user_input.append(
                json_dumps(
                    dict(
                        user_id=sender_id,
                        timestamp=datetime.fromtimestamp(
                            post["create_at"] / 1000, timezone.utc
                        ).isoformat(),
                        message=message,
                    ),
                    indent=2,
                )
            )

            tools = []
            if settings.TAVILY_API_KEY:
                tools.append(
                    tavily_search_tool(
                        api_key=settings.TAVILY_API_KEY,
                    )
                )

            agent = Agent(
                model=await create_model_for_user(mm_user),
                system_prompt=DARK_DIHYAI_PROMPT.format(agent_name=self.me.first_name),
                deps_type=Dependency,
                toolsets=[toolset],
                tools=tools,
            )
            agent.system_prompt(dynamic=True)(mm_system_prompt)

            deps = Dependency(
                channel=channel,
                users={
                    user.id: user
                    async for user in MMUser.objects.filter(membership__channel=channel)
                },
            )

            await self.user_typing(channel_id)
            async with agent.iter(user_input, message_history=history, deps=deps) as r:
                async for node in r:
                    if agent.is_call_tools_node(node):
                        for part in node.model_response.parts:
                            if part.part_kind == "text":
                                await self.post_message(
                                    channel.id,
                                    root_id,
                                    part.content,
                                )

                if r.result:
                    await thread.append_interaction(post_id, r.result)
                else:
                    await self.post_message(
                        channel_id=channel_id,
                        root_id=root_id,
                        message="Failed to generate a response.",
                    )

        except Exception as e:
            logfire.error(f"Error processing posted event: {e}")
            await self.post_message(
                channel_id=channel_id,
                root_id=root_id,
                message=f"An error occurred while processing your message.\n```\n{e}\n```",
            )

    async def on_user_added(self, data, broadcast, seq):
        user_id = data["user_id"]
        channel_id = broadcast["channel_id"]

        try:
            await MMUser.objects.aget(id=user_id)
        except MMUser.DoesNotExist:
            user_data = await self.get_user(user_id)
            await MMUser.objects.acreate(
                id=user_id,
                username=user_data.username,
                nickname=user_data.nickname,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
            )

        try:
            await MMChannel.objects.aget(id=channel_id)
        except MMChannel.DoesNotExist:
            channel_data = await self.get_channel(channel_id)
            await MMChannel.objects.acreate(
                id=channel_id,
                team_id=channel_data.team_id,
                type=channel_data.type,
                name=channel_data.name,
                display_name=channel_data.display_name,
                header=channel_data.header,
                purpose=channel_data.purpose,
            )

        await MMMembership.objects.aupdate_or_create(
            channel_id=channel_id,
            user_id=user_id,
        )

    async def on_user_updated(self, data, broadcast, seq):
        user_data = data["user"]
        await MMUser.objects.aupdate_or_create(
            id=user_data["id"],
            defaults={
                "username": user_data["username"],
                "nickname": user_data["nickname"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
            },
        )

    async def on_channel_updated(self, data, broadcast, seq):
        channel_data = json_loads(data["channel"])
        await MMChannel.objects.aupdate_or_create(
            id=channel_data["id"],
            defaults={
                "team_id": channel_data["team_id"],
                "type": channel_data["type"],
                "name": channel_data["name"],
                "display_name": channel_data["display_name"],
                "header": channel_data["header"],
                "purpose": channel_data["purpose"],
            },
        )
