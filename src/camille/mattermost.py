import logging
import random
from asyncio import create_task
from collections.abc import Mapping
from json import loads
from typing import Any, Optional

import logfire
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.signing import TimestampSigner
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from httpx import AsyncClient
from httpx_ws import AsyncWebSocketSession, aconnect_ws
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MattermostUser(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str


class Mattermost:
    def __init__(self):
        self.client_htt = AsyncClient(
            base_url=settings.MATTERMOST_BASE_URL + "/api/v4",
            headers={"Authorization": f"Bearer {settings.MATTERMOST_API_TOKEN}"},
        )
        self.client_ws: Optional[AsyncWebSocketSession] = None
        self.me: Optional[MattermostUser] = None
        self.current_seq = -1

    async def __aenter__(self):
        await self.client_htt.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client_htt.__aexit__(exc_type, exc_val, exc_tb)

    async def run(self):
        self.me = MattermostUser(**(await self.client_htt.get("/users/me")).json())
        logger.info(
            "Logged in as @%s (ID: %s)",
            self.me.username,
            self.me.id,
        )

        async with aconnect_ws("websocket", self.client_htt) as ws:
            self.client_ws = ws
            while True:
                event = await ws.receive_json()
                self.current_seq = max(self.current_seq, event["seq"])

                # Concurrently handle events
                create_task(self.handle_event(event["event"], event["data"]))

    async def handle_event(self, kind: str, data: Mapping[str, Any]):
        if (handler := getattr(self, f"on_{kind.replace(' ', '_')}", None)) is not None:
            await handler(data)

    @logfire.instrument("on_posted")
    async def on_posted(self, data: Mapping[str, Any]):
        # Not mentioned, not a DM, not a group DM, so ignore
        if self.me.id not in data.get("mentions", ""):
            return

        post_data = loads(data["post"])
        sender_mm_id = post_data["user_id"]

        # Don't respond to our own messages
        if sender_mm_id == self.me.id:
            return

        logger.info("Received post from user ID %s", sender_mm_id)

        channel_id = post_data["channel_id"]
        channel_type = data["channel_type"]
        root_id = post_data["root_id"] or post_data["id"]
        message = post_data["message"]

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

        await self.send_message(
            channel_id,
            "TODO",
            root_id=root_id,
        )
        return

    async def send_message(
        self, channel_id: str, message: str, root_id: Optional[str] = None
    ):
        data = {"channel_id": channel_id, "message": message}
        if root_id is not None:
            data["root_id"] = root_id

        await self.client_htt.post(
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
