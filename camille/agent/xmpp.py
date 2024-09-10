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

from collections.abc import Iterable

from channels.db import database_sync_to_async
from slixmpp import ClientXMPP

from camille.agent.base import Agent
from camille.models import LLMConversation, XMPPChannel


class XmppAgent(Agent):
    def __init__(
        self,
        jid: str,
        password: str,
        channels: Iterable[str],
        name: str,
        window_size: int,
    ):
        self.joined_channels = set()
        self.channels = channels
        super().__init__(name=name, window_size=window_size)
        self.xmpp = ClientXMPP(jid=jid, password=password)
        self.xmpp.register_plugin("xep_0045")  # MUC
        self.xmpp.register_plugin("xep_0030")  # Service Discovery
        self.xmpp.register_plugin("xep_0199")  # Ping

        # Register event handlers
        self.xmpp.add_event_handler("session_start", self.on_session_start)
        self.xmpp.add_event_handler("groupchat_message", self.on_groupchat_message)
        self.xmpp.add_event_handler("groupchat_subject", self.on_groupchat_subject)

    def run(self):
        self.xmpp.connect()
        self.xmpp.process(forever=False)

    async def on_session_start(self, event):
        self.xmpp.send_presence()
        await self.xmpp.get_roster()

        # Join MUC channels
        for channel in self.channels:
            print(f"Joining channel {channel}")
            await self.xmpp.plugin["xep_0045"].join_muc(channel, self.name)

    @database_sync_to_async
    def on_groupchat_message(self, msg):
        # Ignore our own message
        sender = msg["from"].resource
        if sender == self.name:
            return

        channel = XMPPChannel.objects.get_or_create(jid=msg["from"].bare)[0]
        message_body = msg["body"]
        try:
            self.handle_content(channel.conversation, sender, message_body)
        except Exception as e:
            self.send_message(channel.conversation, f"Error: {e}")

    def send_message(self, conversation: LLMConversation, content: str):
        self.xmpp.send_message(
            mto=conversation.xmpp_channel.jid,
            mbody=content if content else "/me has nothing to say",
            mtype="groupchat",
        )

    @database_sync_to_async
    def on_groupchat_subject(self, msg):
        # The subject is sent when updated or joining a channel
        # Use the later to detect joining
        channel_jid = msg["from"]
        if channel_jid not in self.joined_channels:
            self.joined_channels.add(channel_jid)

            xmpp_channel = XMPPChannel.objects.get_or_create(jid=channel_jid)[0]
            msg.reply(
                f"{self.name} is ready! / model '{xmpp_channel.conversation.llm_model}'"
            ).send()
