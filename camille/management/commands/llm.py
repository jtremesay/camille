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
import google.generativeai as genai
from django.core.management.base import BaseCommand

from camille import llm_tools
from camille import settings as camille_settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        model = genai.GenerativeModel(
            camille_settings.GOOGLE_MODEL,
            tools=[llm_tools.get_weather_for_location],
            system_instruction=camille_settings.LLM_PROMPT,
        )
        chat = model.start_chat(enable_automatic_function_calling=True)

        try:
            while True:
                try:
                    user_input = input("You: ")
                except EOFError:
                    break

                response = chat.send_message(user_input)
                print(response)
                self.stdout.write(self.style.SUCCESS(f"Camille: {response.text}"))

        except KeyboardInterrupt:
            pass

        print(chat.history)
