from httpx import AsyncClient
from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset

from camille.ai.deps import Dependency


async def get_model_for_current_user(ctx: RunContext[Dependency]) -> str:
    """Get the LLM model for the current user.

    Returns:
        The LLM model for the user.
    """
    return ctx.deps.sender.model


async def set_model_for_current_user(ctx: RunContext[Dependency], model_name: str):
    """Set the LLM model for the current user.

    Known to work models:

    - `google-gla:gemini-flash-latest`
    - `mistral:mistral-medium-latest`
    - `bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0`

    Args:
        model_name: The name of the model to set for the user.
    """
    user = ctx.deps.sender
    user.model = model_name

    await user.asave()


model_toolset = FunctionToolset(
    [
        get_model_for_current_user,
        set_model_for_current_user,
    ],
    id="camille.user.model",
)


async def list_prompts_of_current_user(
    ctx: RunContext[Dependency],
) -> list[tuple[str, str, str]]:
    """List available personality prompts for the current user.

    Returns:
        A list of available personality prompts for the user.
    """
    user = ctx.deps.sender
    return [
        (pp.name, pp.description, pp.prompt_template)
        async for pp in user.personality_prompts.order_by("name")
    ]


async def get_prompt_of_current_user(
    ctx: RunContext[Dependency], prompt_name: str
) -> tuple[str, str, str]:
    """Get a personality prompt template for the current user.

    Args:
        prompt_name: The name of the personality prompt.

    Returns:
        A tuple of (name, description, prompt_template) for the personality prompt.
    """
    user = ctx.deps.sender
    pp = await user.personality_prompts.aget(name=prompt_name)
    return pp.name, pp.description, pp.prompt_template


async def create_prompt_for_current_user(
    ctx: RunContext[Dependency], name: str, description: str, prompt_template: str
):
    """Create a new personality prompt for the current user.

    Update any existing prompt with the same name.

    Args:
        name: The name of the personality prompt.
        description: The description of the personality prompt.
        prompt_template: The prompt template.
    """
    user = ctx.deps.sender
    await user.personality_prompts.aupdate_or_create(
        name=name,
        defaults={
            "description": description,
            "prompt_template": prompt_template,
        },
    )


async def del_prompt_for_current_user(ctx: RunContext[Dependency], name: str):
    """Delete a personality prompt for the current user.

    Args:
        name: The name of the personality prompt to delete.
    """
    user = ctx.deps.sender
    await user.personality_prompts.filter(name=name).adelete()


async def use_prompt_for_current_user(ctx: RunContext[Dependency], name: str):
    """Set the current personality prompt for the current user.

    Args:
        name: The name of the personality prompt to use.
    """
    user = ctx.deps.sender
    pp = await user.personality_prompts.aget(name=name)
    user.prompt = pp
    await user.asave()


async def get_current_prompt_for_current_user(
    ctx: RunContext[Dependency],
) -> tuple[str, str, str] | None:
    """Get the current personality prompt for the current user.

    Returns:
        A tuple of (name, description, prompt_template) for the current personality prompt,
        or None if no prompt is set.
    """
    user = ctx.deps.sender
    pp = user.prompt
    if pp is None:
        return None
    return pp.name, pp.description, pp.prompt_template


prompt_toolset = FunctionToolset(
    [
        list_prompts_of_current_user,
        get_prompt_of_current_user,
        create_prompt_for_current_user,
        del_prompt_for_current_user,
        use_prompt_for_current_user,
        get_current_prompt_for_current_user,
    ],
    id="camille.user.prompt",
)


async def get_notes_for_current_user(ctx: RunContext[Dependency]) -> str:
    """Get your notes about the current user.

    Returns:
        The notes about the user.
    """
    return ctx.deps.sender.notes


async def set_notes_for_current_user(ctx: RunContext[Dependency], notes: str):
    """Set your notes about the current user.

    Args:
        notes: The notes about the user.
    """
    user = ctx.deps.sender
    user.notes = notes

    await user.asave()


note_toolset = FunctionToolset(
    [
        get_notes_for_current_user,
        set_notes_for_current_user,
    ],
    id="camille.user.notes",
)


async def get_url_content(url: str) -> bytes:
    """Get the content of a URL.

    Args:
        url: The URL to get the content of.

    Returns:
        The content of the URL.
    """
    async with AsyncClient() as client:
        r = await client.get(url)
        r.raise_for_status()

        return r.content


fetch_toolset = FunctionToolset(
    [
        get_url_content,
    ],
    id="camille.fetch",
)

toolsets = [
    model_toolset,
    prompt_toolset,
    note_toolset,
    fetch_toolset,
]
