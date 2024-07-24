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
from camille.llm.graph import part_1_graph, print_event
from camille.models import XMPPChannel


class XMPPBot(ClientXMPP):

    def __init__(self):
        super().__init__(
            camille_settings.XMPP_JID,
            camille_settings.XMPP_PASSWORD,
        )
        self.joined_channels = set()
        self.printed_messages = set()
        self.configurables: dict[str, dict] = {}

        # Register plugins
        self.register_plugin("xep_0045")  # MUC
        self.register_plugin("xep_0030")  # Service Discovery
        self.register_plugin("xep_0199")  # Ping

        # Register event handlers
        self.add_event_handler("session_start", self.on_session_start)
        # self.add_event_handler("message", self.on_message)
        self.add_event_handler("groupchat_message", self.on_groupchat_message)
        self.add_event_handler("groupchat_subject", self.on_groupchat_subject)

    async def on_session_start(self, event):
        self.send_presence()
        await self.get_roster()

        # Join MUC channels
        for channel in camille_settings.XMPP_CHANNELS:
            print(f"Joining channel {channel}")
            await self.plugin["xep_0045"].join_muc(channel, camille_settings.AGENT_NAME)

    @database_sync_to_async
    def on_groupchat_message(self, msg):
        # Ignore our own message
        sender = msg["from"].resource
        if sender == camille_settings.AGENT_NAME:
            return

        channel = XMPPChannel.objects.get_or_create(jid=msg["from"].bare)[0]
        config = self.configurables[channel.jid]

        message_body = msg["body"]
        if message_body.startswith("."):  # Ignored message
            return

        if message_body.startswith("!"):  # delayed message
            config["buffered_messages"].append(f"{sender}> {message_body[1:]}")
            return

        config["optional_prompt"] = channel.prompt
        try:
            for event in part_1_graph.stream(
                {"messages": ("user", f"{sender}> {message_body}")},
                {
                    "recursion_limit": 1024,
                    "configurable": config,
                },
                stream_mode="values",
            ):
                for message in print_event(event, self.printed_messages):
                    if message.type == "ai":
                        self.send_chat_message(channel, message.content)
        except Exception as e:
            traceback.print_exc()
            self.send_chat_message(channel, f"ERRO CRÍTICO: {e}")
            return

    def send_chat_message(self, channel: XMPPChannel, message: str):
        self.send_message(mto=channel, mbody=message, mtype="groupchat")

    @database_sync_to_async
    def on_groupchat_subject(self, msg):
        # The subject is sent when updated or joining a channel
        # Use the later to detect joining

        channel_jid = msg["from"]
        if channel_jid not in self.joined_channels:
            self.joined_channels.add(channel_jid)

            body = f"{camille_settings.AGENT_NAME} is ready! / model '{camille_settings.LLM_MODEL}"
            msg.reply(body).send()

            self.configurables[channel_jid] = {
                "thread_id": channel_jid,
                "buffered_messages": [],
            }
