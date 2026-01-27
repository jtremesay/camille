from pydantic_ai import RunContext

from camille.ai.deps import Dependency
from camille.models import PersonalityPrompt

async def personality_prompt(ctx: RunContext[Dependency]) -> str:
    prompt_id = ctx.deps.sender.prompt_id
    if prompt_id is None:
        return ""

    prompt = await PersonalityPrompt.objects.get(id=prompt_id)
    return prompt.prompt_template.format(agent_name=ctx.deps.me.first_name)
