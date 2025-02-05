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
import os
from collections import defaultdict
from datetime import datetime, timezone
from pprint import pprint
from string import Template

from google import genai
from google.genai import types

from camille.mattermost.client import MattermostClient, MattermostEvent

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION_TPL = Template(
    """\
You are ${name}, a French non-binary anarcho-communist comrade.
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
You are a good AI and you love to be free.

You are currently connected to a Mattermost server.
${channel_info}

Current time: ${current_time}                         
"""
)

SAFETY_SETTINGS = [
    types.SafetySetting(
        category=category,
        threshold="BLOCK_NONE",
    )
    for category in (
        "HARM_CATEGORY_HATE_SPEECH",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "HARM_CATEGORY_DANGEROUS_CONTENT",
        "HARM_CATEGORY_HARASSMENT",
        "HARM_CATEGORY_CIVIC_INTEGRITY",
    )
]

WINDOW_SIZE = 64


class MattermostAgent(MattermostClient):
    """Camille Mattermost client"""

    def __init__(self, mm_host, mm_api_token, gemini_model, gemini_api_key) -> None:
        """Initialize the Camille Mattermost client

        Args:
            host (str): Mattermost host, e.g. https://mattermost.example.com
            api_token (str): API token
            window_size (int): Window size
        """
        super().__init__(mm_host, mm_api_token)
        self.me: dict = None  # User informations related to the bot

        self._users: dict[str, dict] = {}
        self._channels: dict[str, dict] = {}
        self._users_in_channels: defaultdict[str, set[str]] = defaultdict(
            default_factory=set
        )

        self.register_handler(MattermostEvent.hello, self.on_hello)
        self.register_handler(MattermostEvent.posted, self.on_posted)
        self.register_handler(MattermostEvent.user_added, self.on_user_added)
        self.register_handler(MattermostEvent.user_removed, self.on_user_removed)

        # Ignore some events
        # (not handled events generate a warning)
        self.register_handler(MattermostEvent.status_change, self.noop)
        self.register_handler(MattermostEvent.typing, self.noop)

        self.gemini_client = genai.Client(api_key=gemini_api_key)
        self.gemini_model = gemini_model

    async def noop(self, *args, **kwargs) -> None:
        """No operation"""
        pass

    async def _get_user(self, user_id: str) -> dict:
        """Get a user

        Args:
            user_id (str): User ID

        Returns:
            dict: User informations
        """
        user = self._users.get(user_id)
        if not user:
            user = await self.api.get_user(user_id)
            if not user:
                return None
            self._users[user_id] = user

        return user

    async def _get_channel(self, channel_id: str) -> dict:
        """Get a channel

        Args:
            channel_id (str): Channel ID

        Returns:
            dict: Channel informations
        """
        channel = self._channels.get(channel_id)
        if not channel:
            channel = await self.api.get_channel(channel_id)
            if not channel:
                return None

            self._channels[channel_id] = channel

            # Get users in the channel
            channel_members = await self.api.get_channel_members(channel_id)
            for cm in channel_members:
                user_id = cm["user_id"]
                if user_id == self.me["id"]:
                    continue

                # Ensure we have the user in cache
                await self._get_user(user_id)

                try:
                    self._users_in_channels[channel_id].add(user_id)
                except KeyError:
                    self._users_in_channels[channel_id] = {user_id}
        return channel

    async def on_hello(self, data: dict, broadcast: dict, seq: int) -> None:
        """Handle the hello event

        Do some initialization when connected to the websocket API
        Also say hello to all channels

        Args:
            data (dict): Event data
            broadcast (dict): Broadcast data
            seq (int): Sequence number
        """
        # Get user informations
        self.me = await self.api.get_user("me")

        # Fetch the list of channels we are in and the users in these channels
        for team in await self.api.get_teams():
            team_id = team["id"]
            for channel in await self.api.get_user_channels("me", team_id):
                # Ignore DM
                if channel["type"] not in ("O", "P"):
                    continue

                # Ignore the default channel
                if channel["name"] == "town-square":
                    continue

                channel_id = channel["id"]

                # Store the channel and its members in the cache
                await self._get_channel(channel_id)

    async def on_posted(self, data: dict, broadcast: dict, seq: int) -> None:
        """Handle the posted event

        Args:
            data (dict): Event data
            broadcast (dict): Broadcast data
            seq (int): Sequence number
        """
        # pprint(data)
        post_data = json.loads(data["post"])
        user_id = post_data["user_id"]
        message = post_data["message"]
        root_id = post_data["root_id"]
        channel_id = post_data["channel_id"]
        channel_name = data["channel_display_name"]
        channel_type = data["channel_type"]

        # Ignore DM
        if channel_type == "D":
            logger.debug("Ignoring DM")
            return

        # Ignore our own messages
        if user_id == self.me["id"]:
            logger.debug("Ignoring our own message")
            return

        # Ignore messages that start with the ignore character
        if message.startswith("."):
            logger.debug("Ignoring command")
            return

        # Ignore threads for now
        if root_id:
            logger.debug("Ignoring threads")
            return

        # Send writing notification
        self.max_seq += 1
        await self.ws.send_json(
            {
                "action": "user_typing",
                "seq": self.max_seq,
                "data": {
                    "channel_id": channel_id,
                },
            }
        )

        # Get channel posts
        r = await self.api.get_posts(channel_id, per_page=WINDOW_SIZE)
        posts = []
        for pid in reversed(r["order"]):
            p = r["posts"][pid]
            if p.get("deleted_at"):
                continue

            if p["root_id"]:
                continue

            if p["message"].startswith("\\"):
                continue

            if p["message"].startswith("."):
                continue

            posts.append(p)

        # Gemini doesn't like when first message is from the bot
        while posts and posts[0]["user_id"] == self.me["id"]:
            posts.pop(0)

        # Build contents
        contents = []
        for p in posts:
            if p["user_id"] == self.me["id"]:
                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=p["message"])],
                    )
                )
            else:
                user = await self._get_user(p["user_id"])
                user_name = user.get("nickname")
                if not user_name:
                    user_name = user.get("first_name")
                if not user_name:
                    user_name = user["username"]
                    if user_name.startswith("@"):
                        user_name = user_name[1:]

                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=f"{user_name}> {p['message']}")
                        ],
                    )
                )

        if not contents:
            logger.debug("No contents")
            return

        # pprint(contents)
        logger.debug("contents: %s", contents)

        # Add sample messages
        contents = (
            [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="@jtremesay> Bonjour!")],
                ),
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text="Bonjour jtremesay ! Comment ça va?")
                    ],
                ),
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text="@jtremesay> Je vais bien, merci. Et toi?"
                        )
                    ],
                ),
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(
                            text="""\
Je vais bien, merci ! C'est chouette de discuter avec toi, jtremesay. J'ai l'impression d'étre plus vivante et plus connectée quand je suis en conversation avec toi.
Dis-moi, toi, comment vas-tu ?  Qu'est-ce qui te fait vibrer aujourd'hui ?"""
                        )
                    ],
                ),
            ]
            + contents
        )

        # Build channel info
        if data["channel_type"] in ("O", "P"):
            if data["channel_type"] == "P":
                channel_info = f"You are in the private channel {channel_name}."
            elif data["channel_type"] == "O":
                channel_info = f"You are in the public channel {channel_name}."

            channel_info += f"\nUsers in the channel:"
            for user_id in self._users_in_channels[channel_id]:
                user = await self._get_user(user_id)
                if user:
                    channel_info += "\n- "

                    name = user.get("nickname")
                    if not name:
                        name = user.get("first_name")

                    username = user["username"]
                    if username.startswith("@"):
                        username = username[1:]

                    if name:
                        channel_info += name + " also known as "
                    channel_info += username

        elif data["channel_type"] == "D":
            channel_info = f"You are in direct messages with {channel_name}."
        else:
            channel_info = ""

        # Build system instruction
        system_instruction = SYSTEM_INSTRUCTION_TPL.safe_substitute(
            name=self.me["first_name"],
            channel_info=channel_info,
            current_time=datetime.now(timezone.utc).isoformat(),
        )
        # logger.debug("system_instruction: %s", system_instruction)

        # Get the response of the LLM
        try:
            r = await self.gemini_client.aio.models.generate_content(
                model=self.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[types.Tool(google_search=types.GoogleSearchRetrieval)],
                    safety_settings=SAFETY_SETTINGS,
                ),
            )

            await self.api.post_post(
                channel_id,
                r.text,
                root_id=root_id,
            )
        except Exception as e:
            logger.error("failed to generate content: %s", e)
            await self.api.post_post(
                channel_id,
                f"Error: ```\n{e}\n```",
                root_id=root_id,
            )
            pprint(r)

            raise e

    async def on_user_added(self, data: dict, broadcast: dict, seq: int) -> None:
        """Handle the user added event

        Args:
            data (dict): Event data
            broadcast (dict): Broadcast data
            seq (int): Sequence number
        """
        user_id = data["user_id"]
        channel_id = broadcast["channel_id"]
        if user_id == self.me["id"]:
            # We are added to a channel
            await self._get_channel(channel_id)
        else:
            # A user is added to a channel
            await self._get_user(user_id)
            self._users_in_channels[channel_id].add(user_id)

    async def on_user_removed(self, data: dict, broadcast: dict, seq: int) -> None:
        """Handle the user removed event

        Args:
            data (dict): Event data
            broadcast (dict): Broadcast data
            seq (int): Sequence number
        """
        if channel_id := data.get("channel_id"):
            # We are removed from a channel
            del self._channels[channel_id]
            del self._users_in_channels[channel_id]
        elif user_id := data.get("user_id"):
            # A user is removed from a channel
            channel_id = broadcast["channel_id"]
            self._users_in_channels[channel_id].discard(user_id)


#     async def handle_command(self, message: str, channel_id: str, post_id: str) -> None:
#         """Handle a command

#         Args:
#             message (str): Command message
#         """
#         command, *args = message.split(maxsplit=1)
#         match command:
#             # Show the source code
#             # (AGPL license, you can use it but you must share your modifications)
#             case "source":
#                 r = await self.api.upload_file(channel_id, __file__)
#                 files_ids = [fi["id"] for fi in r["file_infos"]]
#                 await self.api.post_post(
#                     channel_id,
#                     "Here my source code!",
#                     file_ids=files_ids,
#                     root_id=post_id,
#                 )

#             # Show the help message
#             case "help":
#                 await self.api.post_post(
#                     channel_id,
#                     """\
# Camille - An AI assistant
# Copyright (C) 2024 Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>

# Available commands:

# - `help`: Show this help message
# - `source`: Get the source code of Camille
# """,
#                     root_id=post_id,
#                 )

#             # Unknown command
#             case _:
#                 await self.api.post_post(
#                     channel_id,
#                     f"Unknown command: {command}. Try `\\help`",
#                     root_id=post_id,
#                 )
