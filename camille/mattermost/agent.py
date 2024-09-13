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
from datetime import datetime, timezone
from enum import StrEnum
from pprint import pprint
from string import Template

import google.generativeai as genai
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory

from camille.mattermost.client import MattermostClient, MattermostEvent

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION_TPL = Template(
    """\
You are ${name}, a French non-binary anarcho-communist assistant.
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
${channel_instruction}
Current time: ${current_time}                         
"""
)

SAFETY_SETTINGS = {
    c: HarmBlockThreshold.BLOCK_NONE
    for c in (
        HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        HarmCategory.HARM_CATEGORY_HARASSMENT,
    )
}

WINDOW_SIZE = 64


class GeminiModel(StrEnum):
    flash = "gemini-1.5-flash"
    pro = "gemini-1.5-pro"


DEFAULT_MODEL = GeminiModel.flash


class MattermostAgent(MattermostClient):
    """Camille Mattermost client"""

    def __init__(self, host, api_token) -> None:
        """Initialize the Camille Mattermost client

        Args:
            host (str): Mattermost host, e.g. https://mattermost.example.com
            api_token (str): API token
            window_size (int): Window size
        """
        super().__init__(host, api_token)
        self.me: dict = None  # User informations related to the bot
        
        self._users: dict[str, dict] = {}
        self._channels: dict[str, dict] = {}
        self._users_in_channels: dict[str, list[str]] = {}

        self.register_handler(MattermostEvent.hello, self.on_hello)
        self.register_handler(MattermostEvent.posted, self.on_posted)

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

                self._channels[channel["id"]] = channel

                # Get users in the channel
                channel_members = await self.api.get_channel_members(channel["id"])
                for cm in channel_members:
                    user_id = cm["user_id"]
                    if user_id == self.me["id"]:
                        continue

                    self._users_in_channels.setdefault(channel["id"], []).append(
                        user_id
                    )

                    if not self._users.get(user_id):
                        self._users[user_id] = await self.api.get_user(user_id)

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
        post_id = post_data["id"]
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
                    {
                        "role": "model",
                        "parts": [p["message"]],
                    }
                )
            else:
                user = self._users.get(p["user_id"])
                user_name = user.get("nickname")
                if not user_name:
                    user_name = user.get("first_name")
                if not user_name:
                    user_name = user["username"]
                    if user_name.startswith("@"):
                        user_name = user_name[1:]

                contents.append(
                    {
                        "role": "user",
                        "parts": [f"{user_name}> {p["message"]}"],
                    }
                )

        if not contents:
            logger.debug("No contents")
            return

        # pprint(contents)
        logger.debug("contents: %s", contents)

        # Build channel info
        if data["channel_type"] in ("O", "P"):
            if data["channel_type"] == "P":
                channel_info = f"You are in the private channel {channel_name}."
            elif data["channel_type"] == "O":
                channel_info = f"You are in the public channel {channel_name}."

            channel_info += f"\nUsers in the channel:"
            for user_id in self._users_in_channels.get(channel_id, []):
                user = self._users.get(user_id)
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
            channel_instruction="",
            current_time=datetime.now(timezone.utc).isoformat(),
        )
        logger.debug("system_instruction: %s", system_instruction)

        # Get the response of the LLM
        try:
            model = genai.GenerativeModel(
                DEFAULT_MODEL,
                safety_settings=SAFETY_SETTINGS,
                system_instruction=system_instruction,
            )

            r = await model.generate_content_async(
                contents=contents,
            )

            try:
                canditate = r.candidates[0]
            except IndexError:
                return

            content = canditate.content.parts[0].text
            logger.debug("content: %s", content)
            # pprint(content)
        except Exception as e:
            logger.error("failed to generate content: %s", e)
            await self.api.post_post(
                channel_id,
                f"Error: ```\n{e}\n```",
                root_id=root_id,
            )
            pprint(r)

            raise e

        await self.api.post_post(
            channel_id,
            content,
            root_id=root_id,
        )

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