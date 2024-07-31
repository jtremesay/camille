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
import traceback

from channels.db import database_sync_to_async
from slixmpp import ClientXMPP

from camille import settings as camille_settings
from camille.llm import LLMModel, graph, print_event
from camille.models import XMPPChannel


class XMPPBot(ClientXMPP):

    def __init__(self):
        if not camille_settings.XMPP_JID or not camille_settings.XMPP_PASSWORD:
            raise ValueError("XMPP_JID and XMPP_PASSWORD must be set")

        super().__init__(
            camille_settings.XMPP_JID,
            camille_settings.XMPP_PASSWORD,
        )
        self.joined_channels = set()
        self.printed_messages = set()

        # Register plugins
        self.register_plugin("xep_0045")  # MUC
        self.register_plugin("xep_0030")  # Service Discovery
        self.register_plugin("xep_0199")  # Ping

        # Register event handlers
        self.add_event_handler("session_start", self.on_session_start)
        self.add_event_handler("message", self.on_message)
        self.add_event_handler("groupchat_message", self.on_groupchat_message)
        self.add_event_handler("groupchat_subject", self.on_groupchat_subject)

    async def on_session_start(self, event):
        self.send_presence()
        await self.get_roster()

        # Join MUC channels
        for channel in camille_settings.XMPP_CHANNELS:
            print(f"Joining channel {channel}")
            await self.plugin["xep_0045"].join_muc(channel, camille_settings.AGENT_NAME)

    def handle_command(self, command: str, channel: XMPPChannel) -> bool | str:
        if not command or not command.startswith("\\"):
            return False

        command = command[1:].strip()
        try:
            command_name, args = command.split(" ", 1)
        except ValueError:
            command_name = command
            args = ""

        if command_name == "help":
            return """\
Commands: 
\\help                       Show this help
\\prompt                     Show current prompt
\\set_prompt <new_prompt>    Change current prompt
\\llm                        Show current LLM model
\\set_llm <new_llm>          Change current LLM model
\\llms                       List available LLM models
"""

        if command_name == "prompt":
            return f"Prompt: {channel.prompt}"

        if command_name == "set_prompt":
            channel.prompt = args
            channel.save(update_fields=["prompt"])

            return f"Prompt set to: {channel.prompt}"

        if command_name == "llm":
            return f"LLM model: {channel.llm_model}"

        if command_name == "set_llm":
            if args not in dict(LLMModel.choices):
                return f"Invalid LLM model: {args}"

            channel.llm_model = args
            channel.save(update_fields=["llm_model"])

            return f"LLM model set to: {channel.llm_model}"

        if command_name == "llms":
            return "Available LLM models: " + ", ".join(sorted(LLMModel))

        return "Unknown command"

    def handle_message(self, msg, is_muc: bool):
        channel = XMPPChannel.objects.get_or_create(jid=msg["from"].bare)[0]
        message_body = msg["body"]

        message_body = msg["body"]
        if message_body.startswith("."):  # Ignored message
            return

        if isinstance(response := self.handle_command(message_body, channel), str):
            if response:
                self.send_chat_message(channel, response)
            return

        config = {
            "thread_id": channel.jid,
            "is_muc": is_muc,
            "optional_prompt": channel.prompt,
            "model_name": channel.llm_model,
        }

        try:
            for event in graph.stream(
                {"messages": ("user", message_body)},
                {
                    "recursion_limit": camille_settings.RECURSION_LIMIT,
                    "configurable": config,
                },
                stream_mode="values",
            ):
                for message in print_event(event, self.printed_messages):
                    if message.type == "ai":
                        msg.reply(message.content).send()
        except Exception as e:
            traceback.print_exc()
            self.send_chat_message(channel, f"ERRO CRÍTICO: {e}")
            return

    @database_sync_to_async
    def on_message(self, msg):
        if msg["type"] not in ("chat", "normal"):
            return

        self.handle_message(msg, is_muc=False)

    @database_sync_to_async
    def on_groupchat_message(self, msg):
        # Ignore our own message
        sender = msg["from"].resource
        if sender == camille_settings.AGENT_NAME:
            return

        self.handle_message(msg, is_muc=True)

    def send_chat_message(self, channel: XMPPChannel, message: str):
        self.send_message(mto=channel, mbody=message, mtype="groupchat")

    @database_sync_to_async
    def on_groupchat_subject(self, msg):

        # The subject is sent when updated or joining a channel
        # Use the later to detect joining

        channel_jid = msg["from"]
        if channel_jid not in self.joined_channels:
            self.joined_channels.add(channel_jid)
            channel = XMPPChannel.objects.get_or_create(jid=channel_jid)[0]

            body = (
                f"{camille_settings.AGENT_NAME} is ready! / model '{channel.llm_model}'"
            )
            msg.reply(body).send()
