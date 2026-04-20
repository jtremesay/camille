# Camille - An AI assistant
# Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import random
from asyncio import create_task
from collections.abc import Mapping
from datetime import datetime
from json import dumps, loads
from typing import Any, Optional
from zoneinfo import ZoneInfo

import logfire
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import TimestampSigner
from django.db import close_old_connections
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from httpx import AsyncClient
from httpx_ws import AsyncWebSocketSession, aconnect_ws
from pydantic_ai import Agent, TextPart
from pydantic_ai.capabilities import WebFetch, WebSearch

from camille.ai.capabilities.conversation import ConversationCapability
from camille.ai.capabilities.current_time import CurrentTimeCapability
from camille.ai.capabilities.instructions import InstructionsCapability
from camille.ai.capabilities.mattermost import MattermostCapability
from camille.ai.capabilities.memory import MemoryCapability
from camille.ai.capabilities.personality import PersonalityCapability
from camille.ai.deps import MattermostDeps
from camille.ai.models import NoCredentialsError, create_model_for_user
from camille.models import AgentConfig, MattermostConversation


def get_client() -> AsyncClient:
    return AsyncClient(
        base_url=settings.MATTERMOST_BASE_URL + "/api/v4",
        headers={"Authorization": f"Bearer {settings.MATTERMOST_API_TOKEN}"},
    )


class Mattermost:
    def __init__(self):
        self.client_http = get_client()
        self.client_ws: Optional[AsyncWebSocketSession] = None
        self.me_mm_id: Optional[str] = None
        self.me_name: Optional[str] = None
        self.current_seq = 0
        self.agent = Agent(
            deps_type=MattermostDeps,
            capabilities=[
                PersonalityCapability(),
                ConversationCapability(),
                MattermostCapability(),
                InstructionsCapability(),
                MemoryCapability(),
                CurrentTimeCapability(),
                WebSearch(builtin=False),
                WebFetch(builtin=False),
            ],
        )

    async def __aenter__(self):
        await self.client_http.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client_http.__aexit__(exc_type, exc_val, exc_tb)

    async def run(self):
        me = (await self.client_http.get("/users/me")).json()
        self.me_mm_id = me["id"]
        self.me_name = me["first_name"] or me["username"]
        async with aconnect_ws("websocket", self.client_http) as ws:
            self.client_ws = ws
            while True:
                event = await ws.receive_json()
                if kind := event.get("event"):
                    # Concurrently handle events
                    create_task(self.handle_event(kind, event["data"]))

    async def handle_event(self, kind: str, data: Mapping[str, Any]):
        if (handler := getattr(self, f"on_{kind.replace(' ', '_')}", None)) is not None:
            await sync_to_async(close_old_connections)()
            await handler(data)

    @logfire.instrument("on_posted")
    async def on_posted(self, data: Mapping[str, Any]):
        # Not mentioned, not a DM, not a group DM, so ignore
        if self.me_mm_id not in data.get("mentions", ""):
            return

        # Ignore messages from non-users (like "System")
        if not data["sender_name"].startswith("@"):
            return

        post_data = loads(data["post"])
        sender_mm_id = post_data["user_id"]

        # Don't respond to our own messages
        if sender_mm_id == self.me_mm_id:
            return

        channel_id = post_data["channel_id"]
        channel_type = data["channel_type"]
        root_id = post_data["root_id"] or post_data["id"]
        message = post_data["message"]

        conversation = None
        try:
            try:
                user = await User.objects.aget(mm_binding__mm_id=sender_mm_id)
            except User.DoesNotExist:
                user = None

            # Handle commands
            if await self.handle_commands(
                channel_type,
                message,
                user,
                channel_id,
                root_id,
                sender_mm_id,
            ):
                return

            if user is None:
                await self.send_message(
                    channel_id,
                    "Your Mattermost account is not linked to any user account. Please send `!/link` in DM to link your account.",
                    root_id=root_id,
                )
                return

            agent_config = await AgentConfig.objects.aget(user=user)
            if agent_config.model is None:
                await self.send_message(
                    channel_id,
                    "Your agent is not configured with a model. Please set a model in your agent config.",
                    root_id=root_id,
                )
                return

            try:
                model = await create_model_for_user(user, agent_config.model)
            except NoCredentialsError:
                await self.send_message(
                    channel_id,
                    "Your agent is not configured with the necessary credentials. Please set the credentials in your agent config.",
                    root_id=root_id,
                )
                return

            user_prompt = {
                "user_id": user.id,
                "message": message,
                "datetime": datetime.fromtimestamp(
                    post_data["create_at"] / 1000, tz=ZoneInfo(settings.TIME_ZONE)
                ).isoformat(),
            }

            post_metadata = post_data.get("metadata", {})
            if files_data := post_metadata.get("files", []):
                files = []
                for file in files_data:
                    files.append({
                        "id": file["id"],
                        "name": file["name"],
                        "size": file["size"],
                        "mime_type": file["mime_type"],
                    })
                user_prompt["files"] = files

            deps = MattermostDeps(
                agent_name=self.me_name,
                current_user=user,
                all_users=[
                    user
                    async for user in User.objects.filter(
                        mm_binding__mm_id__in=[
                            m["user_id"]
                            for m in (
                                await self.client_http.get(
                                    f"/channels/{channel_id}/members"
                                )
                            ).json()
                        ]
                    )
                ],
                channel_id=channel_id,
                channel_name=data["channel_display_name"],
                mattermost_client=self.client_http,
            )

            conversation, _ = await MattermostConversation.objects.aget_or_create(
                root_id=root_id,
                defaults={"channel_id": channel_id},
            )

            await self.user_typing(channel_id)

            async with self.agent.iter(
                dumps(user_prompt),
                deps=deps,
                model=model,
                message_history=await conversation.amessages(),
            ) as run:
                async for node in run:
                    if self.agent.is_call_tools_node(node):
                        for part in node.model_response.parts:
                            if isinstance(part, TextPart):
                                await self.send_message(
                                    channel_id,
                                    part.content,
                                    root_id=root_id,
                                    file_ids=deps.generated_files_ids,
                                )
                                deps.generated_files_ids.clear()

                await conversation.runs.acreate(
                    user=user,
                    messages_json=run.new_messages_json(),
                )
        except Exception as e:
            await self.send_message(
                channel_id,
                f"An error occurred while processing your message. Please try again later.\nError details: {e}",
                root_id=root_id,
            )

        # If the conversation has no runs, delete it to save space
        if conversation and not await conversation.runs.aexists():
            await conversation.adelete()

    async def send_message(
        self,
        channel_id: str,
        message: str,
        root_id: Optional[str] = None,
        file_ids: Optional[list[str]] = None,
    ):
        data = {"channel_id": channel_id, "message": message}
        if root_id is not None:
            data["root_id"] = root_id

        if file_ids:
            data["file_ids"] = file_ids

        await self.client_http.post(
            "/posts",
            json=data,
        )

    async def handle_commands(
        self,
        channel_type: str,
        message: str,
        user: Optional[User],
        channel_id: str,
        root_id: Optional[str],
        sender_mm_id: str,
    ) -> bool:
        if channel_type != "D" or not message.startswith("!/"):
            return False

        command = message[2:]
        match command:
            case "link":
                if user is not None:
                    await self.send_message(
                        channel_id,
                        "Your Mattermost account is already linked to a user account.",
                        root_id=root_id,
                    )
                    return True

                token = TimestampSigner().sign_object({
                    "mm_id": sender_mm_id,
                    "nonce": random.randint(0, 2**64 - 1),
                })
                url = f"https://{settings.MAIN_HOST}{reverse('mattermost_bind')}?token={token}"
                await self.send_message(
                    channel_id,
                    f"Please use the following link to link your Mattermost account: {url}",
                    root_id=root_id,
                )

            case "reset_password":
                if user is None:
                    await self.send_message(
                        channel_id,
                        "Your Mattermost account is not linked to any user account. Please send `!/link` in DM to link your account.",
                        root_id=root_id,
                    )
                    return True

                uidb64 = urlsafe_base64_encode(
                    force_bytes(User._meta.pk.value_to_string(user))
                )
                token = default_token_generator.make_token(user)
                url = f"https://{settings.MAIN_HOST}{reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})}"
                await self.send_message(
                    channel_id,
                    f"Please use the following link to reset your password: {url}",
                    root_id=root_id,
                )

            case "help":
                await self.send_message(
                    channel_id,
                    """\
Available commands:

- `!/help`: Show this message.
- `!/link`: Link your Mattermost account to a user account.
- `!/reset_password`: Generate a password reset link for your user account. Only works if your Mattermost account is linked to a user account.
""",
                    root_id=root_id,
                )

            case _:
                await self.send_message(
                    channel_id,
                    f"Unknown command: `{command}`. Please send `!/help` for a list of available commands.",
                    root_id=root_id,
                )

        return True

    async def ws_send(self, action: str, data: dict) -> None:
        self.current_seq += 1
        await self.client_ws.send_json({
            "action": action,
            "data": data,
            "seq": self.current_seq,
        })

    async def user_typing(self, channel_id: str) -> None:
        await self.ws_send("user_typing", {"channel_id": channel_id})
