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
from os import getlogin

from camille.agent.base import Agent
from camille.models import LLMConversation, SHSession


class ShellAgent(Agent):
    def __init__(self, name: str, window_size: int):
        super().__init__(name=name, window_size=window_size)
        self.username = getlogin()

    def handle_message(self, message: str):
        # Get the shell session
        session = SHSession.objects.get_or_create(username=self.username)[0]

        # Handle the message
        conversation = session.conversation
        sender = session.username
        self.handle_content(conversation, sender, message)

    def send_message(self, conversation: LLMConversation, content: str):
        print(content)

    def run(self):
        try:
            while True:
                user_input = input("> ")
                if user_input.lower() in ["quit", "exit", "q"]:
                    break

                self.handle_message(user_input)
        except (KeyboardInterrupt, EOFError):
            pass
