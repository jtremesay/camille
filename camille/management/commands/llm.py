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

from datetime import datetime, timezone
from os import getlogin

from django.core.management.base import BaseCommand
from langchain_core.messages import BaseMessage, HumanMessage

from camille.llm import LLMModel, invoke_llm


class Command(BaseCommand):
    def handle(self, *args, **options):
        messages: list[BaseMessage] = []
        username = getlogin()

        try:
            while True:
                user_input = input("> ")
                if user_input.lower() in ["quit", "exit", "q"]:
                    break

                messages.append(
                    HumanMessage(
                        f"{datetime.now(tz=timezone.utc).isoformat()}|{username}> {user_input}"
                    )
                )

                result = invoke_llm(LLMModel.GEMINI_FLASH, messages)
                messages.append(result)
                print(result.content)
        except (KeyboardInterrupt, EOFError):
            pass

        print("Goodbye!")
