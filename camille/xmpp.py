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
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.db import connection
from slixmpp import ClientXMPP

from camille import settings as camille_settings
from camille.llm import Agent, Messages, SystemMessage
from camille.models import LLMRole, XMPPChannel, XMPPMessage


def get_llm_messages_for_channel(channel: XMPPChannel) -> Messages:
    llm_messages = Messages()
    llm_messages |= SystemMessage(camille_settings.LLM_PROMPT)

    # Build the history of messages
    xmpp_llm_messages = Messages()
    for xmpp_message in channel.messages.order_by("-timestamp")[
        : camille_settings.LLM_MESSAGES_COUNT
    ]:
        xmpp_llm_messages |= xmpp_message.as_message()

    # assistant messages before first user message are not allowed :(
    while (
        xmpp_llm_messages.messages
        and xmpp_llm_messages.messages[-1].role == LLMRole.ASSISTANT
    ):
        xmpp_llm_messages.messages.pop()

    llm_messages |= reversed(xmpp_llm_messages)

    return llm_messages


class XMPPBot(ClientXMPP):

    def __init__(self):
        super().__init__(
            camille_settings.XMPP_JID,
            camille_settings.XMPP_PASSWORD,
        )
        self.joined_channels = set()
        self.agent = Agent()

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
            await self.plugin["xep_0045"].join_muc(channel, camille_settings.NAME)

    @database_sync_to_async
    def on_groupchat_message(self, msg):
        # Ignore our own message
        sender = msg["from"].resource
        if sender == camille_settings.NAME:
            return

        channel = XMPPChannel.objects.get_or_create(jid=msg["from"].bare)[0]
        message_body = msg["body"]

        is_mention_message = False
        if message_body.startswith("."):
            message_body = message_body[1:]
            is_mention_message = True

        # Save the message
        XMPPMessage.objects.create(
            channel=channel,
            sender=sender,
            role=LLMRole.USER,
            content=message_body,
        )

        if is_mention_message:
            # Build the history of messages
            llm_messages = get_llm_messages_for_channel(channel)
            try:
                response = self.agent.process(camille_settings.LLM_MODEL, llm_messages)
            except Exception as e:
                self.send_chat_message(channel, f"ERRO CRÍTICO: {e}")
                return

            if response is None:
                return

            XMPPMessage.from_message(channel, camille_settings.NAME, response).save()

            self.send_chat_message(channel, response.content)

    def send_chat_message(self, channel: XMPPChannel, message: str):
        self.send_message(mto=channel, mbody=message, mtype="groupchat")

    @database_sync_to_async
    def on_groupchat_subject(self, msg):
        # The subject is sent when updated or joining a channel
        # Use the later to detect joining

        channel_jid = msg["from"]
        if channel_jid not in self.joined_channels:
            self.joined_channels.add(channel_jid)

            body = f"{camille_settings.NAME} is ready! / model '{camille_settings.LLM_MODEL}' / {camille_settings.LLM_MESSAGES_COUNT} msgs"
            msg.reply(body).send()
