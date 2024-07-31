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

import asyncio
import uuid
from typing import Any

from django.core.management.base import BaseCommand

import camille.settings as camille_settings
from camille.llm import LLMModel, graph, print_event

config = {
    "recursion_limit": camille_settings.RECURSION_LIMIT,
    "configurable": {
        # Checkpoints are accessed by thread_id
        "thread_id": str(uuid.uuid4()),
        "model_name": LLMModel.GEMINI_FLASH,
    },
}


class Command(BaseCommand):
    def handle(self, *args, **options):
        _printed = set()
        while True:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            for event in graph.stream(
                {"messages": ("user", user_input)}, config, stream_mode="values"
            ):
                print_event(event, _printed)
