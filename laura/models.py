# LAURA - Language Analysis and Understanding Robot Assistant
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

import laura.settings as laura_settings
from laura.agent import Agent, AIMessage, BaseMessage, HumanMessage, SystemMessage


class XMPPChannel(models.Model):
    jid = models.CharField(max_length=255, unique=True)
    model = models.CharField(max_length=255, null=True, blank=True, default=None)
    prompt = models.TextField(null=True, blank=True, default=None)

    def get_model(self):
        if self.model is None:
            return laura_settings.LLM_MODEL

        return self.model

    def get_prompt(self):
        if self.prompt is None:
            return laura_settings.LLM_PROMPT

        return self.prompt

    def __str__(self):
        return self.jid


class XMPPMessage(models.Model):
    channel = models.ForeignKey(XMPPChannel, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    sender = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    body = models.TextField()

    def as_message(self) -> BaseMessage:
        if self.role == "system":
            return SystemMessage(self.body)
        if self.role == "assistant":
            return AIMessage(self.body)
        else:
            return HumanMessage(f"{self.sender} says: {self.body}")

    @classmethod
    def from_message(cls, channel: XMPPChannel, sender: str, message: BaseMessage):
        return cls(
            channel=channel,
            sender=sender,
            role=message.role,
            body=message.content,
        )
