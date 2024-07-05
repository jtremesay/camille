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

from camille.llm import AIMessage, BaseMessage, HumanMessage, SystemMessage


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

    def as_message(self) -> BaseMessage:
        if self.role == LLMRole.SYSTEM:
            return SystemMessage(self.body)
        if self.role == LLMRole.ASSISTANT:
            return AIMessage(self.content)
        else:
            return HumanMessage(f"{self.sender} says: {self.content}")

    @classmethod
    def from_message(cls, channel: XMPPChannel, sender: str, message: BaseMessage):
        return cls(
            channel=channel,
            sender=sender,
            role=message.role,
            content=message.content,
        )
