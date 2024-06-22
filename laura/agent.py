import json
import pprint
from collections.abc import Iterable
from typing import Optional, Union

from openai import OpenAI

from laura import settings as laura_settings


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
        return cls(laura_settings.LLM_PROMPT)


class AIMessage(BaseMessage):
    def __init__(self, content):
        super().__init__("assistant", content)


class Agent:
    def __init__(self):
        self.openai = OpenAI(
            api_key=laura_settings.OPENAI_API_KEY,
            base_url=laura_settings.OPENAI_BASE_URL,
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
