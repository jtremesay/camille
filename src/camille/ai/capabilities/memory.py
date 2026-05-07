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
from camille.models import AgentMemory


class MemoryToolset(FunctionToolset):
    def __init__(self):
        super().__init__(id="memory")

        @self.tool()
        async def create_memory(ctx: RunContext[Deps], content: str) -> None:
            """Create a new memory for the current user with the given content.

            :param content: The content of the memory to create.
            """

            await AgentMemory.objects.acreate(
                user=ctx.deps.current_user, content=content
            )

        @self.tool()
        async def update_memory(ctx: RunContext[Deps], id: int, content: str) -> None:
            """Update the content of an existing memory for the current user.

            :param id: The ID of the memory to update.
            :param content: The new content for the memory.
            """
            memory = await AgentMemory.objects.aget(id=id, user=ctx.deps.current_user)
            memory.content = content
            await memory.asave(update_fields=["content"])

        @self.tool()
        async def delete_memory(ctx: RunContext[Deps], id: int) -> None:
            """Delete an existing memory for the current user.

            :param id: The ID of the memory to delete.
            """
            memory = await AgentMemory.objects.aget(id=id, user=ctx.deps.current_user)
            await memory.adelete()


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
                    "current_user": ctx.deps.current_user,
                },
            )

        return inner
