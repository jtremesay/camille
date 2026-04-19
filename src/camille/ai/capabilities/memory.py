# Camille - An AI assistant
# Copyright (C) Jonathan Tremesaygues <jonathan.tremesaygues@slaanesh.org>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from typing import Any

from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from pydantic_ai import FunctionToolset, RunContext
from pydantic_ai.capabilities import AbstractCapability

from camille.ai.deps import Deps


class MemoryToolset(FunctionToolset):
    def __init__(self):
        super().__init__(id="memory")

        @self.tool()
        @sync_to_async
        def set_memory_for_current_user(ctx: RunContext[Deps], notes: str) -> None:
            """Set your memory notes for the current user."""
            config = ctx.deps.current_user.agent_config
            config.notes = notes
            config.save(update_fields=["notes"])

        @self.tool()
        @sync_to_async
        def append_memory_for_current_user(ctx: RunContext[Deps], notes: str) -> None:
            """Append to your memory notes for the current user."""
            config = ctx.deps.current_user.agent_config
            config.notes += "\n" + notes
            config.save(update_fields=["notes"])

        @self.tool()
        @sync_to_async
        def search_and_replace_memory_for_current_user(
            ctx: RunContext[Deps], search: str, replace: str
        ) -> None:
            """Search and replace in your memory notes for the current user.

            :param search: The string to search for in the memory notes.
            :param replace: The string to replace the search string with in the memory notes.
            """
            config = ctx.deps.current_user.agent_config
            config.notes = config.notes.replace(search, replace)
            config.save(update_fields=["notes"])


class MemoryCapability(AbstractCapability):
    def get_toolset(self) -> MemoryToolset:
        return MemoryToolset()

    def get_instructions(self) -> Any:
        @sync_to_async
        def inner(ctx: RunContext[Deps]) -> str:
            return render_to_string(
                "camille/ai/instructions/memory.md",
                {
                    "all_users": ctx.deps.all_users,
                },
            )

        return inner
