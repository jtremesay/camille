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

from collections.abc import Mapping, Sequence
from typing import Optional

from openai import OpenAI

from camille import settings as camille_settings


class Agent:
    def __init__(self):
        self.openai = OpenAI(
            api_key=camille_settings.OPENAI_API_KEY,
            base_url=camille_settings.OPENAI_BASE_URL,
        )

    def process(self, model: str, messages: Sequence[Mapping]) -> str:
        print(">", model, messages[-1]["content"])
        completion = self.openai.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
        )

        try:
            response = completion.choices[0].message.content
        except AttributeError:
            raise RuntimeError("Unexpected response from OpenAI", completion.choices)

        print("<", response)

        return response
