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

import pprint
from datetime import datetime

from camille.llm import LLMModel, get_llm
from camille.models import LLMConversation, LLMMessage


class Agent:
    def __init__(self, name: str, window_size: int):
        self.name = name
        self.window_size = window_size

    def handle_command(self, conversation: LLMConversation, command: str):
        try:
            command_name, args = command.split(" ", 1)
        except ValueError:
            command_name = command
            args = ""

        if command_name == "help":
            self.send_message(
                conversation,
                """\
Commands: 
\\help                       Show this help
\\prompt                     Show current prompt
\\set_prompt <new_prompt>    Change current prompt
\\llm                        Show current LLM model
\\set_llm <new_llm>          Change current LLM model
\\llms                       List available LLM models
""",
            )
            return

        if command_name == "prompt":
            self.send_message(conversation, conversation.prompt)
            return

        if command_name == "set_prompt":
            conversation.prompt = args
            conversation.save(update_fields=["prompt"])

            self.send_message(conversation, "Prompt set")
            return

        if command_name == "llm":
            self.send_message(conversation, conversation.llm_model)
            return

        if command_name == "set_llm":
            if args not in dict(LLMModel.choices):
                self.send_message(conversation, "Invalid LLM model")
                return

            conversation.llm_model = args
            conversation.save(update_fields=["llm_model"])

            self.send_message(conversation, "LLM model set")
            return

        if command_name == "llms":
            self.send_message(
                conversation, "Available LLM models: " + ", ".join(sorted(LLMModel))
            )
            return

        self.send_message(conversation, "Unknown command")

    def handle_content(
        self, conversation: LLMConversation, sender: str, content: str
    ) -> LLMMessage:
        if content.startswith("."):
            return

        if content.startswith("\\"):
            self.handle_command(conversation, content[1:].strip())
            return

        LLMMessage.objects.create(
            conversation=conversation, sender=sender, content=content
        )

        response = self.handle_conversation(conversation)

        return response

    def handle_conversation(self, conversation: LLMConversation) -> LLMMessage:
        # Get last messages
        messages = list(
            reversed(conversation.messages.order_by("-timestamp")[: self.window_size])
        )

        # Remove firsts messages if the conversation is started by the agent
        # (some services like Google Gemini force the user to start the conversation)
        while messages and messages[0].is_agent:
            messages.pop(0)

        messages = [m.as_lc() for m in messages]

        print("<<<<<<<<<<<<<<<<")
        pprint.pprint(messages)

        # Invoke the LLM model
        llm = get_llm(conversation.llm_model)
        response = llm.invoke(
            {
                "messages": messages,
                "optional_prompt": conversation.prompt,
                "current_time": datetime.now().strftime("%H:%M:%S, %a %d %B %Y"),
            }
        )
        print(">>>>>>>>>>>>>>>>")
        pprint.pprint(response)

        LLMMessage.objects.create(
            conversation=conversation,
            is_agent=True,
            sender=self.name,
            content=response.content,
        )
        self.send_message(conversation, response.content)

        return response

    def send_message(self, conversation: LLMConversation, content: str):
        raise NotImplementedError
