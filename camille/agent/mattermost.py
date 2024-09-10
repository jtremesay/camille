# Camille - An AI assistant
# Copyright (C) 2024 Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import json
from typing import Any, Mapping

from aiohttp import ClientSession
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async

from camille.agent.base import Agent
from camille.models import LLMConversation, MMChannel


class MattermostAgent(Agent):
    def __init__(self, host, api_token, name, window_size):
        super().__init__(name=name, window_size=window_size)
        self.session = ClientSession(
            base_url=host,
            headers={"Authorization": "Bearer " + api_token},
        )
        self.ws = None
        self.user_id = None
        self.seq = 0

    async def arun(self):
        async with self.session.ws_connect("/api/v4/websocket") as ws:
            self.ws = ws
            async for message in ws:
                message = json.loads(message.data)
                if "seq_reply" in message:
                    continue

                seq = max(message.get("seq", 0), self.seq)
                if event := message.get("event"):
                    match message["event"]:
                        case "hello":
                            await self.on_hello()
                        case "posted":
                            await self.on_posted(message)
                else:
                    print(message)
            self.ws = None

    @database_sync_to_async
    def aget_channel(self, channel_id: str):
        return self.get_channel(channel_id)

    def get_channel(self, channel_id: str):
        channel = MMChannel.objects.get_or_create(mmid=channel_id)[0]
        return channel, channel.conversation

    async def on_hello(self):
        self.user_id = (await self.aget("/api/v4/users/me"))["id"]
        for team_data in await self.aget("/api/v4/teams"):
            team_id = team_data["id"]
            for channel_data in await self.aget(
                f"/api/v4/users/me/teams/{team_id}/channels"
            ):
                if channel_data["type"] in ("O", "P"):
                    if channel_data["name"] == "town-square":
                        continue

                    channel_id = channel_data["id"]
                    _, conversation = await self.aget_channel(channel_id)
                    await self.apost(
                        f"/api/v4/posts",
                        {
                            "channel_id": channel_id,
                            "message": f"{self.name} is ready! / model '{conversation.llm_model}'",
                        },
                    )

    async def on_posted(self, message):
        message_data = message["data"]
        channel_name = message_data["channel_name"]

        # Ignore messages from the default channel
        if channel_name == "town-square":
            return

        # Ignore messages from the bot itself
        post_data = json.loads(message_data["post"])
        sender_id = post_data["user_id"]
        if sender_id == self.user_id:
            return

        channel_id = post_data["channel_id"]
        _, conversation = await self.aget_channel(channel_id)
        message_body = post_data["message"]
        sender_name = message_data["sender_name"]

        self.seq += 1
        await self.ws.send_json(
            {
                "action": "user_typing",
                "seq": self.seq,
                "data": {
                    "channel_id": channel_id,
                    "parent_id": "",
                },
            }
        )
        await self.ahandle_message(conversation, sender_name, message_body)

    @database_sync_to_async
    def ahandle_message(self, conversation: LLMConversation, sender: str, message: str):
        self.handle_content(conversation, sender, message)

    async def aget(self, path: str):
        return await (await self.session.get(path)).json()

    async def apost(self, path: str, data: Mapping[str, Any]):
        return await (await self.session.post(path, json=data)).json()

    @async_to_sync
    async def post(self, path: str, data: Mapping[str, Any]):
        return await (await self.session.post(path, json=data)).json()

    def send_message(self, conversation: LLMConversation, content: str):
        self.post(
            "/api/v4/posts",
            {
                "channel_id": conversation.mm_channel.mmid,
                "message": content,
            },
        )
