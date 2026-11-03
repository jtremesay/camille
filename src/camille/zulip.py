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
import re
from asyncio import Task, create_task, sleep
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from json import dumps
from mimetypes import guess_type
from posixpath import basename
from typing import Any
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
from httpx import AsyncClient, HTTPError, Timeout
from pydantic_ai import TextPart, ToolCallPart
from pydantic_ai.messages import FilePart

from camille.ai.agent import create_agent_from_config
from camille.ai.capabilities.zulip import ZulipCapability
from camille.ai.deps import ZulipDeps
from camille.ai.models import NoCredentialsError, create_model_for_user
from camille.models import AgentConfig, ZulipConversation

# Zulip refuses messages longer than this
MAX_MESSAGE_LENGTH = 10000

# Links to uploaded files, as written in the raw markdown of a message
UPLOAD_LINK_RE = re.compile(r"\[([^\]]*)\]\((/user_uploads/[^)\s]+)\)")

NOT_LINKED_MESSAGE = (
    "Your Zulip account is not linked to any user account. "
    "Please send `!/link` to me in a direct message to link your account."
)


class ZulipError(Exception):
    def __init__(self, code: str | None, msg: str):
        super().__init__(msg)
        self.code = code


def get_client() -> AsyncClient:
    return AsyncClient(
        base_url=settings.ZULIP_SITE.rstrip("/") + "/api/v1",
        auth=(settings.ZULIP_EMAIL, settings.ZULIP_API_KEY),
        # Long enough for the long polling of the events endpoint
        timeout=Timeout(30, read=120),
    )


@dataclass
class Target:
    """Where a message comes from, and where to reply."""

    # Channel (stream) message
    stream_id: int | None = None
    topic: str | None = None
    # Direct message: all participants, the bot included
    participant_ids: tuple[int, ...] = ()

    @property
    def is_direct(self) -> bool:
        return self.stream_id is None

    @property
    def key(self) -> str:
        """Identify the conversation (thread) this message belongs to."""
        if self.is_direct:
            return "dm:" + ",".join(str(i) for i in sorted(self.participant_ids))
        return f"stream:{self.stream_id}:{self.topic}"


class Zulip:
    def __init__(self):
        self.client = get_client()
        self.me_id: int | None = None
        self.me_name: str | None = None
        self.tasks: set[Task] = set()

    async def __aenter__(self):
        await self.client.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def api(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        r = await self.client.request(method, url, **kwargs)
        try:
            data = r.json()
        except ValueError:
            r.raise_for_status()
            raise
        if data.get("result") != "success":
            raise ZulipError(data.get("code"), data.get("msg", r.text))

        return data

    async def run(self):
        me = await self.api("GET", "/users/me")
        self.me_id = me["user_id"]
        self.me_name = me["full_name"]

        while True:
            try:
                await self.listen()
            except (HTTPError, ZulipError) as e:
                logfire.warning("Zulip event queue failed: {error}", error=str(e))
                await sleep(5)

    async def listen(self):
        """Register an event queue and dispatch its events until it expires."""
        queue = await self.api(
            "POST",
            "/register",
            data={
                "event_types": dumps(["message"]),
                # Get the raw markdown, like the users wrote it
                "apply_markdown": "false",
            },
        )
        queue_id = queue["queue_id"]
        last_event_id = queue["last_event_id"]

        while True:
            try:
                data = await self.api(
                    "GET",
                    "/events",
                    params={"queue_id": queue_id, "last_event_id": last_event_id},
                )
            except ZulipError as e:
                if e.code == "BAD_EVENT_QUEUE_ID":
                    # The queue was garbage collected by the server
                    return
                logfire.warning("Zulip events polling failed: {error}", error=str(e))
                await sleep(5)
                continue
            except HTTPError as e:
                # Transient network error, keep the same queue to not lose events
                logfire.warning("Zulip events polling failed: {error}", error=str(e))
                await sleep(5)
                continue

            for event in data["events"]:
                last_event_id = max(last_event_id, event["id"])
                if event["type"] == "message":
                    # Concurrently handle messages
                    task = create_task(
                        self.on_message(event["message"], event.get("flags", []))
                    )
                    self.tasks.add(task)
                    task.add_done_callback(self.tasks.discard)

    @logfire.instrument("on_message")
    async def on_message(self, message: Mapping[str, Any], flags: list[str]):
        await sync_to_async(close_old_connections)()

        sender_id = message["sender_id"]

        # Don't respond to our own messages
        if sender_id == self.me_id:
            return

        if message["type"] == "private":
            target = Target(
                participant_ids=tuple(u["id"] for u in message["display_recipient"])
            )
            member_ids = list(target.participant_ids)
            channel_name = (
                "a direct message conversation"
                if len(member_ids) <= 2
                else "a group direct message conversation"
            )
        else:
            # Not mentioned in a channel, so ignore
            if "mentioned" not in flags:
                return

            target = Target(stream_id=message["stream_id"], topic=message["subject"])
            channel_name = (
                f'the channel "#{message["display_recipient"]}", '
                f'topic "{message["subject"]}"'
            )
            member_ids = []

        content = message["content"]

        conversation = None
        try:
            try:
                user = await User.objects.aget(zulip_binding__zulip_id=str(sender_id))
            except User.DoesNotExist:
                user = None

            # Handle commands
            if await self.handle_commands(target, content, user, sender_id):
                return

            if user is None:
                await self.send_message(target, NOT_LINKED_MESSAGE)
                return

            agent_config = await AgentConfig.objects.select_related("user").aget(
                user=user
            )
            if agent_config.model is None:
                await self.send_message(
                    target,
                    "Your agent is not configured with a model. Please set a model in your agent config.",
                )
                return

            try:
                model = await create_model_for_user(user, agent_config.model)
                agent = await create_agent_from_config(
                    agent_config, capabilities=[ZulipCapability()]
                )
            except NoCredentialsError:
                await self.send_message(
                    target,
                    "Your agent is not configured with the necessary credentials. Please set the credentials in your agent config.",
                )
                return

            user_prompt = {
                "user_id": user.id,
                "message": content,
                "datetime": datetime.fromtimestamp(
                    message["timestamp"], tz=ZoneInfo(settings.TIME_ZONE)
                ).isoformat(),
            }

            if links := UPLOAD_LINK_RE.findall(content):
                user_prompt["files"] = [
                    {
                        "id": path,
                        "name": name or basename(path),
                        "mime_type": guess_type(path)[0]
                        or "application/octet-stream",
                    }
                    for name, path in links
                ]

            if not target.is_direct:
                member_ids = (
                    await self.api("GET", f"/streams/{target.stream_id}/members")
                )["subscribers"]

            deps = ZulipDeps(
                agent_name=self.me_name,
                current_user=user,
                all_users=[
                    user
                    async for user in User.objects.filter(
                        zulip_binding__zulip_id__in=[str(i) for i in member_ids]
                    )
                ],
                channel_name=channel_name,
                zulip_client=self.client,
            )

            conversation, _ = await ZulipConversation.objects.aget_or_create(
                key=target.key
            )

            await self.user_typing(target)

            async with agent.iter(
                dumps(user_prompt),
                deps=deps,
                model=model,
                message_history=await conversation.amessages(),
            ) as run:
                async for node in run:
                    if agent.is_call_tools_node(node):
                        # Upload the files first so they can be linked in the
                        # message, whatever their position in the response
                        for part in node.model_response.parts:
                            if isinstance(part, FilePart):
                                await deps.upload_file(part.content)

                        for part in node.model_response.parts:
                            if agent_config.debug_tools and isinstance(
                                part, ToolCallPart
                            ):
                                await self.send_message(
                                    target,
                                    f"(calling tool `{part.tool_name}` with args: `{dumps(part.args)}`)",
                                )
                            elif isinstance(part, TextPart):
                                await self.send_message(
                                    target,
                                    self.with_files(part.content, deps),
                                )

                # Files that were not linked in any message
                if deps.generated_files:
                    await self.send_message(target, self.with_files("", deps))

                await conversation.runs.acreate(
                    user=user,
                    messages_json=run.new_messages_json(),
                )
        except Exception as e:
            logfire.exception("Failed to handle Zulip message")
            await self.send_message(
                target,
                f"An error occurred while processing your message. Please try again later.\nError details: {e}",
            )

        # If the conversation has no runs, delete it to save space
        if conversation and not await conversation.runs.aexists():
            await conversation.adelete()

    @staticmethod
    def with_files(content: str, deps: ZulipDeps) -> str:
        """Append links to the generated files to a message, and forget them."""
        links = "\n".join(f"[{name}]({path})" for name, path in deps.generated_files)
        deps.generated_files.clear()
        return "\n\n".join(part for part in (content, links) if part)

    async def send_message(self, target: Target, content: str):
        if target.is_direct:
            data = {"type": "private", "to": dumps(list(target.participant_ids))}
        else:
            data = {"type": "stream", "to": target.stream_id, "topic": target.topic}

        # Long messages are split, preferably on line breaks
        while content.strip():
            chunk = content[:MAX_MESSAGE_LENGTH]
            if len(content) > MAX_MESSAGE_LENGTH and (cut := chunk.rfind("\n")) > 0:
                chunk = chunk[:cut]
            content = content[len(chunk) :]

            try:
                await self.api("POST", "/messages", data={**data, "content": chunk})
            except (HTTPError, ZulipError) as e:
                logfire.error("Failed to send Zulip message: {error}", error=str(e))
                return

    async def user_typing(self, target: Target) -> None:
        if target.is_direct:
            data = {
                "op": "start",
                "type": "private",
                "to": dumps([i for i in target.participant_ids if i != self.me_id]),
            }
        else:
            data = {
                "op": "start",
                "type": "stream",
                "stream_id": target.stream_id,
                "topic": target.topic,
            }

        # Best effort, the indicator is purely cosmetic
        try:
            await self.api("POST", "/typing", data=data)
        except (HTTPError, ZulipError):
            pass

    async def handle_commands(
        self,
        target: Target,
        content: str,
        user: User | None,
        sender_id: int,
    ) -> bool:
        # Commands are only available in a one-to-one direct message
        if not target.is_direct or len(target.participant_ids) > 2:
            return False
        if not content.startswith("!/"):
            return False

        command = content[2:].strip()
        match command:
            case "link":
                if user is not None:
                    await self.send_message(
                        target,
                        "Your Zulip account is already linked to a user account.",
                    )
                    return True

                token = TimestampSigner().sign_object(
                    {
                        "zulip_id": str(sender_id),
                        "nonce": random.randint(0, 2**64 - 1),
                    }
                )
                url = f"https://{settings.MAIN_HOST}{reverse('zulip_bind')}?token={token}"
                await self.send_message(
                    target,
                    f"Please use the following link to link your Zulip account: {url}",
                )

            case "reset_password":
                if user is None:
                    await self.send_message(target, NOT_LINKED_MESSAGE)
                    return True

                uidb64 = urlsafe_base64_encode(
                    force_bytes(User._meta.pk.value_to_string(user))
                )
                token = default_token_generator.make_token(user)
                url = f"https://{settings.MAIN_HOST}{reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})}"
                await self.send_message(
                    target,
                    f"Please use the following link to reset your password: {url}",
                )

            case "connect":
                if user is None:
                    await self.send_message(target, NOT_LINKED_MESSAGE)
                    return True

                token = TimestampSigner().sign_object(
                    {
                        "user_id": user.id,
                    }
                )
                url = f"https://{settings.MAIN_HOST}{reverse('passwordless_login')}?token={token}"
                await self.send_message(target, f"Click here to connect: {url}")

            case "reset":
                await ZulipConversation.objects.filter(key=target.key).adelete()
                await self.send_message(
                    target, "Done, I forgot this conversation. Let's start fresh!"
                )

            case "help":
                await self.send_message(
                    target,
                    """\
Available commands:

- `!/help`: Show this message.
- `!/link`: Link your Zulip account to a user account.
- `!/connect`: Generate a passwordless login link.
- `!/reset_password`: Generate a password reset link for your user account. Only works if your Zulip account is linked to a user account.
- `!/reset`: Forget the history of this direct message conversation. In a channel, start a new topic instead.
""",
                )

            case _:
                await self.send_message(
                    target,
                    f"Unknown command: `{command}`. Please send `!/help` for a list of available commands.",
                )

        return True
