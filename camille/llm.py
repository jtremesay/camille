#!/usr/bin/env python
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
from typing import Optional, Union

from openai import OpenAI

from camille import settings as camille_settings


class Messages:
    def __init__(self, messages: Optional[list["BaseMessage"]] = None):
        if messages is None:
            messages = []
        else:
            messages = list(messages)
        self.messages = messages

    def serialize(self):
        return [message.serialize() for message in self.messages]

    def __or__(
        self, other: Union["BaseMessage", "Messages", Iterable["BaseMessage"]]
    ) -> "Messages":
        if isinstance(other, Messages):
            return Messages(self.messages + other.messages)

        try:
            return Messages(self.messages + list(other))
        except TypeError as e:
            if isinstance(other, BaseMessage):
                return Messages(self.messages + [other])

            raise e

    def __str__(self):
        return "\n".join(str(message) for message in self.messages)

    def __iter__(self):
        return iter(self.messages)

    def __reversed__(self):
        return Messages(list(reversed(self.messages)))


class BaseMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content

    def serialize(self):
        return {
            "role": self.role,
            "content": self.content,
        }

    def __str__(self):
        return f"{self.role}: {self.content}"


class HumanMessage(BaseMessage):
    def __init__(self, content):
        super().__init__("user", content)


class SystemMessage(BaseMessage):
    def __init__(self, content):
        super().__init__("system", content)

    @classmethod
    def default(cls):
        return cls(camille_settings.LLM_PROMPT)


class AIMessage(BaseMessage):
    def __init__(self, content):
        super().__init__("assistant", content)


class Agent:
    def __init__(self):
        self.openai = OpenAI(
            api_key=camille_settings.OPENAI_API_KEY,
            base_url=camille_settings.OPENAI_BASE_URL,
        )

    def process(self, model: str, messages: Messages) -> Optional[AIMessage]:
        # Generate the response
        serialized_messages = messages.serialize()
        # pprint.pprint(serialized_messages)
        print(">", model, messages.messages[-1].content)
        completion = self.openai.chat.completions.create(
            model=model,
            messages=serialized_messages,
            stream=False,
        )
        try:
            choice = completion.choices[0].message
        except AttributeError:
            raise RuntimeError("Unexpected response from OpenAI", completion.choices)
        # pprint.pprint(choice)

        response = choice.content
        print("<", response)

        return AIMessage(response)
