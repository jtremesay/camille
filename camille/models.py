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
from typing import Union

from django.db import models
from django.db.models.signals import post_delete
from langchain_core.messages import AIMessage, HumanMessage

from camille.llm import LLMModel

###############################################################################
# LLM


class LLMConversation(models.Model):
    llm_model = models.CharField(
        max_length=64,
        choices=LLMModel.choices,
        default=LLMModel.GEMINI_FLASH,
    )
    prompt = models.TextField(default="", blank=True)


def delete_conversation(sender, instance, **kwargs):
    instance.conversation.delete()


class LLMMessage(models.Model):
    conversation = models.ForeignKey(
        LLMConversation, on_delete=models.CASCADE, related_name="messages"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_agent = models.BooleanField(
        default=False
    )  # True if the message is from the agent
    sender = models.CharField(max_length=255)
    content = models.TextField()

    def as_lc(self) -> Union[AIMessage, HumanMessage]:
        if self.is_agent:
            return AIMessage(content=self.content)
        else:
            return HumanMessage(content=f"{self.sender}> {self.content}")


###############################################################################
# XMPP


class XMPPChannel(models.Model):
    jid = models.CharField(max_length=255, unique=True)
    conversation = models.OneToOneField(
        LLMConversation,
        on_delete=models.CASCADE,
        related_name="xmpp_channel",
        related_query_name="xmpp_channel",
        default=LLMConversation.objects.create,
    )

    def __str__(self):
        return self.jid


post_delete.connect(delete_conversation, sender=XMPPChannel)


###############################################################################
# Mattermost


class MMChannel(models.Model):
    mmid = models.CharField(max_length=255, unique=True)
    conversation = models.OneToOneField(
        LLMConversation,
        on_delete=models.CASCADE,
        related_name="mm_channel",
        related_query_name="mm_channel",
        default=LLMConversation.objects.create,
    )

    def __str__(self):
        return self.mmid


post_delete.connect(delete_conversation, sender=MMChannel)

###############################################################################
# Shell


class SHSession(models.Model):
    conversation = models.OneToOneField(
        LLMConversation,
        on_delete=models.CASCADE,
        related_name="shell_session",
        related_query_name="shell_session",
        default=LLMConversation.objects.create,
    )
    username = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.username


post_delete.connect(delete_conversation, sender=SHSession)
