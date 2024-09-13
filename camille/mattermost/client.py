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
import logging
from enum import StrEnum

from aiohttp.http_websocket import WSMsgType

from camille.mattermost.api import MattermostAPIClient

logger = logging.getLogger(__name__)


class MattermostEvent(StrEnum):
    added_to_team = "added_to_team"
    authentication_challenge = "authentication_challenge"
    channel_converted = "channel_converted"
    channel_created = "channel_created"
    channel_deleted = "channel_deleted"
    channel_member_updated = "channel_member_updated"
    channel_updated = "channel_updated"
    channel_viewed = "channel_viewed"
    config_changed = "config_changed"
    delete_team = "delete_team"
    direct_added = "direct_added"
    emoji_added = "emoji_added"
    ephemeral_message = "ephemeral_message"
    group_added = "group_added"
    hello = "hello"
    leave_team = "leave_team"
    license_changed = "license_changed"
    memberrole_updated = "memberrole_updated"
    new_user = "new_user"
    plugin_disabled = "plugin_disabled"
    plugin_enabled = "plugin_enabled"
    plugin_statuses_changed = "plugin_statuses_changed"
    post_deleted = "post_deleted"
    post_edited = "post_edited"
    post_unread = "post_unread"
    posted = "posted"
    preference_changed = "preference_changed"
    preferences_changed = "preferences_changed"
    preferences_deleted = "preferences_deleted"
    reaction_added = "reaction_added"
    reaction_removed = "reaction_removed"
    response = "response"
    role_updated = "role_updated"
    status_change = "status_change"
    typing = "typing"
    update_team = "update_team"
    user_added = "user_added"
    user_removed = "user_removed"
    user_role_updated = "user_role_updated"
    user_updated = "user_updated"
    dialog_opened = "dialog_opened"
    thread_updated = "thread_updated"
    thread_follow_changed = "thread_follow_changed"
    thread_read_changed = "thread_read_changed"


class MattermostClient:
    """A minimal Mattermost client that connects to the websocket API

    client = MattermostClient("https://mattermost.example.com", "api-token")
    await client.run()
    """

    def __init__(self, host: str, api_token: str) -> None:
        """Initialize the Mattermost client

        Note: `.close()` must be called before exiting the asyncio event loop.

        Args:
            host (str): Mattermost host, e.g. https://mattermost.example.com
            api_token (str): API token
        """
        self.api = MattermostAPIClient(host, api_token)
        self.max_seq = 0
        self.events_handlers: dict[MattermostEvent, list[callable]] = {}
        self.register_handler(MattermostEvent.hello, self._on_hello)

    async def close(self) -> None:
        """Close the client

        Must be called before exiting the asyncio event loop
        """
        await self.api.close()

    async def run(self) -> None:
        """Run the client

        Connect to the websocket API and handle events.
        Automatically close the API client when done.
        """

        logger.info(f"Connecting…")
        async with self.api.ws_connect() as ws:
            self.ws = ws
            async for message in ws:
                # Mattermost only sends text messages
                if message.type != WSMsgType.TEXT:
                    logger.warning("ignoring non text message: %s", message)
                    continue

                # Decode the message
                try:
                    payload = json.loads(message.data)
                except json.JSONDecodeError:
                    logger.error("failed to decode message: %s", message)
                    continue

                # Handle the message
                await self.handle_message(payload)
            self.ws = None

    def register_handler(self, event: MattermostEvent, handler: callable) -> None:
        """Register an event handler

        Args:
            event (MattermostEvent): Event type
            handler (callable): Event handler
        """
        self.events_handlers.setdefault(event, []).append(handler)

    async def handle_message(self, payload: dict) -> None:
        """Handle a message from the websocket API

        Args:
            payload (dict): Message payload
        """
        if event := payload.get("event"):
            # Look like a normal event, process it
            broadcast = payload["broadcast"]
            seq = payload["seq"]
            if seq and seq > self.max_seq:
                self.max_seq = seq
            data = payload["data"]
            await self.handle_event(event, data, broadcast, seq)
        elif "seq_reply" in payload:
            # TODO?
            pass
        else:
            logger.warning("message without event: %s", payload)

    async def handle_event(
        self, event: str, data: dict, broadcast: dict, seq: int
    ) -> None:
        """Handle and dispatch an event

        Args:
            event (str): Event type
            data (dict): Event data
            broadcast (dict): Broadcast data
            seq (int): Sequence number
        """
        logger.debug("handling event: %d %s", seq, event)
        try:
            handlers = self.events_handlers[event]
        except KeyError:
            logger.warning(
                "no handler for event: %s %s %s %i", event, data, broadcast, seq
            )
            return

        for handler in handlers:
            await handler(data, broadcast, seq)

    async def _on_hello(self, data: dict, broadcast: dict, seq: int) -> None:
        """Handle the hello event

        Args:
            data (dict): Event data
            broadcast (dict): Broadcast data
            seq (int): Sequence number
        """
        logger.info("Connected")
