from typing import Any

from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability

from camille.ai.deps import MattermostDeps


class MattermostCapability(AbstractCapability):
    def get_instructions(self) -> Any:
        @sync_to_async
        def inner(ctx: RunContext[MattermostDeps]) -> str:
            return render_to_string(
                "camille/ai/instructions/mattermost.md",
                {
                    "channel_name": ctx.deps.channel_name,
                },
            )

        return inner
