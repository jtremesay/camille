from typing import Any

from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from django.utils import timezone
from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability

from camille.ai.deps import Deps


class CurrentTimeCapability(AbstractCapability):
    def get_instructions(self) -> Any:
        @sync_to_async
        def inner(ctx: RunContext[Deps]) -> str:
            return render_to_string(
                "camille/ai/instructions/current_time.md",
                {
                    "current_time": timezone.now(),
                },
            )

        return inner
