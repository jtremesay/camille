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
from django.db import models

from camille import settings as camille_settings


class LLMRole(models.TextChoices):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class XMPPChannel(models.Model):
    # Could be an user or a muc
    jid = models.CharField(max_length=255, unique=True)

    prompt = models.TextField(default="")

    def __str__(self):
        return self.jid

    def llm_messages(self):
        xmpp_messages = list(
            reversed(
                self.messages.order_by("-timestamp")[
                    : camille_settings.LLM_MESSAGES_COUNT
                ]
            )
        )
        print(xmpp_messages)
        while xmpp_messages and xmpp_messages[0].role == LLMRole.ASSISTANT:
            xmpp_messages.pop(0)

        llm_messages = [
            {
                "role": LLMRole.SYSTEM,
                "content": self.prompt if self.prompt else camille_settings.LLM_PROMPT,
            }
        ]
        for xmpp_message in xmpp_messages:
            print(xmpp_message)
            llm_message = {
                "role": xmpp_message.role,
                "content": xmpp_message.content,
            }
            if xmpp_message.role == LLMRole.USER:
                llm_message["name"] = xmpp_message.sender

            llm_messages.append(llm_message)

        return llm_messages


class XMPPMessage(models.Model):
    channel = models.ForeignKey(
        XMPPChannel,
        on_delete=models.CASCADE,
        related_name="messages",
        related_query_name="message",
    )
    sender = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    role = models.CharField(
        max_length=255, choices=LLMRole.choices, default=LLMRole.USER
    )
    content = models.TextField()
