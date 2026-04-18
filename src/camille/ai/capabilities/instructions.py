from typing import Any

from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability

from camille.ai.deps import Deps


class InstructionsCapability(AbstractCapability):
    def get_instructions(self) -> Any:
        @sync_to_async
        def inner(ctx: RunContext[Deps]) -> str:
            return render_to_string(
                "camille/ai/instructions/instructions.md",
                {
                    "all_users": ctx.deps.all_users,
                },
            )

        return inner
