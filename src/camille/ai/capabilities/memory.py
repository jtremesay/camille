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
            config.save()

        @self.tool()
        @sync_to_async
        def append_memory_for_current_user(ctx: RunContext[Deps], notes: str) -> None:
            """Append to your memory notes for the current user."""
            config = ctx.deps.current_user.agent_config
            config.notes += "\n" + notes
            config.save()


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
