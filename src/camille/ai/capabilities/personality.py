from typing import Any

from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability

from camille.ai.deps import Deps


class PersonalityCapability(AbstractCapability):
    def get_instructions(self) -> Any:
        @sync_to_async
        def inner(ctx: RunContext[Deps]) -> str:
            agent_config = ctx.deps.current_user.agent_config
            try:
                prompt_template = agent_config.personality.prompt_template
            except AttributeError:
                prompt_template = "You are {agent_name}."

            return render_to_string(
                "camille/ai/instructions/personality.md",
                {"prompt": prompt_template.format(agent_name=ctx.deps.agent_name)},
            )

        return inner
