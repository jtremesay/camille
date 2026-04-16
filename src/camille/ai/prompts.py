from asgiref.sync import sync_to_async
from pydantic_ai import RunContext

from camille.ai.deps import Dependency
from camille.models import PersonalityPrompt


@sync_to_async
def personality_prompt(ctx: RunContext[Dependency]) -> str:
    prompt_id = ctx.deps.sender.prompt_id
    if prompt_id is None:
        return ""

    return PersonalityPrompt.objects.get(id=prompt_id).prompt_template.format(agent_name=ctx.deps.me.first_name)
