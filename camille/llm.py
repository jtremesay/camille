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

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import google.generativeai as genai
from openai import OpenAI

from camille import llm_tools
from camille import settings as camille_settings
from camille.models import LLMRole, XMPPChannel, XMPPMessage


class Agent:
    def get_last_llm_messages(self, channel: XMPPChannel) -> Iterable[Any]:
        xmpp_messages = self.get_last_xmpp_messages(channel)
        llm_messages = self.llm_messages_from_xmpp_messages(xmpp_messages)

        return llm_messages

    def get_last_xmpp_messages(self, channel: XMPPChannel) -> Iterable[XMPPMessage]:
        return channel.messages.order_by("-timestamp")[
            : camille_settings.LLM_MESSAGES_COUNT
        ][::-1]

    def llm_messages_from_xmpp_messages(
        self, xmpp_messages: Iterable[XMPPChannel]
    ) -> Iterable[Any]:
        for xmpp_message in xmpp_messages:
            llm_message = self.llm_message_from_xmpp_message(xmpp_message)
            yield llm_message

    def llm_message_from_xmpp_message(self, xmpp_message: XMPPMessage) -> Any:
        raise NotImplementedError

    def process(self, channel: XMPPChannel) -> str:
        system_prompt = channel.prompt
        llm_messages = self.get_last_llm_messages(channel)

        return self.process_llm_messages(system_prompt, llm_messages)

    def process_llm_messages(
        self, system_prompt: str, llm_messages: Iterable[Any]
    ) -> str:
        raise NotImplementedError


class AgentOpenAI(Agent):
    def __init__(self):
        self.openai = OpenAI(
            api_key=camille_settings.OPENAI_API_KEY,
            base_url=camille_settings.OPENAI_BASE_URL,
        )

    def llm_message_from_xmpp_message(self, xmpp_message: XMPPMessage) -> Any:
        llm_message = {
            "role": xmpp_message.role,
            "content": xmpp_message.content,
        }
        if xmpp_message.role == LLMRole.USER:
            llm_message["name"] = xmpp_message.sender

        return llm_message

    def process_llm_messages(
        self, system_prompt: str, llm_messages: Iterable[Any]
    ) -> str:
        llm_messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ] + list(llm_messages)

        completion = self.openai.chat.completions.create(
            model=camille_settings.OPENAI_MODEL,
            messages=llm_messages,
            stream=False,
        )

        try:
            response = completion.choices[0].message.content
        except AttributeError:
            raise RuntimeError("Unexpected response from OpenAI", completion.choices)

        return response


genai.configure(api_key=camille_settings.GOOGLE_API_KEY)


class AgentGemini(Agent):
    def llm_message_from_xmpp_message(self, xmpp_message: XMPPMessage) -> Any:

        role = None
        content = None
        if xmpp_message.role == LLMRole.USER:
            role = "user"
            content = f"{xmpp_message.sender}> {xmpp_message.content}"
        else:
            if xmpp_message.role == LLMRole.ASSISTANT:
                role = "model"
            else:
                role = "user"
            content = xmpp_message.content

        llm_message = {"role": role, "parts": [{"text": content}]}
        return llm_message

    def process_llm_messages(
        self, system_prompt: str, llm_messages: Iterable[Any]
    ) -> str:
        llm_messages = list(llm_messages)
        last_llm_message = llm_messages.pop()

        model = genai.GenerativeModel(
            camille_settings.GOOGLE_MODEL,
            tools=[llm_tools.get_weather_for_location],
            system_instruction=system_prompt,
        )
        chat = model.start_chat(
            enable_automatic_function_calling=True, history=llm_messages
        )
        print(">", last_llm_message["parts"][0]["text"])
        response = chat.send_message(last_llm_message)
        print("<", response.text)

        return response.text
