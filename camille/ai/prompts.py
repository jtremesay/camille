from pydantic_ai import RunContext

from camille.ai.deps import Dependency


def personality_prompt(ctx: RunContext[Dependency]) -> str:
    prompt = ctx.deps.sender.prompt
    if prompt is None:
        return ""

    return prompt.prompt_template.format(agent_name=ctx.deps.me.first_name)
