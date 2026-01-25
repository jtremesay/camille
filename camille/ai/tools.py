from httpx import AsyncClient
from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset

from camille.ai.deps import Dependency


async def get_model_for_current_user(ctx: RunContext[Dependency]):
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


async def get_prompt_for_current_user(ctx: RunContext[Dependency]) -> str:
    """Get the personality prompt for the current user.

    Returns:
        The personality prompt for the user.
    """
    return ctx.deps.sender.prompt


async def set_prompt_for_current_user(ctx: RunContext[Dependency], prompt: str):
    """Set the personality prompt for the current user.

    Supported placeholders:

    - `{agent_name}`: The name of the AI agent.

    Args:
        prompt: The personality prompt to set for the current user.
    """
    user = ctx.deps.sender
    user.prompt = prompt

    await user.asave()


prompt_toolset = FunctionToolset(
    [
        get_prompt_for_current_user,
        set_prompt_for_current_user,
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
