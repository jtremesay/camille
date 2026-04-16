from asgiref.sync import sync_to_async
from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset

from camille.ai.deps import Dependency


@sync_to_async
def get_llm_model(ctx: RunContext[Dependency]) -> str:
    """Get the LLM model used by the agent of the current user.
    Returns:
        The LLM model
    """
    return ctx.deps.sender.model


@sync_to_async
def set_llm_model(ctx: RunContext[Dependency], model_name: str):
    """Set the LLM model used by the agent of the current user.

    Known to work models:

    - `google-gla:gemini-flash-latest`
    - `mistral:mistral-medium-latest`
    - `bedrock:eu.anthropic.claude-sonnet-4-5-20250929-v1:0`

    Args:
        model_name: The name of the model
    """
    user = ctx.deps.sender
    user.model = model_name
    user.save()


model_toolset = FunctionToolset(
    [
        get_llm_model,
        set_llm_model,
    ],
    id="camille.agent.model",
)


@sync_to_async
def list_personalities(
    ctx: RunContext[Dependency],
) -> list[str]:
    """List available personalities for the agent of the current user.

    Returns:
        A list of available personalities
    """
    user = ctx.deps.sender
    return list(user.personality_prompts.order_by("name").values_list("name", flat=True))


@sync_to_async
def describe_personality(ctx: RunContext[Dependency], name: str) -> tuple[str, str, str]:
    """Get the description of a personality available for the agent of the current user.

    Args:
        name: The name of the personality.

    Returns:
        A tuple of (name, description, prompt_template)
    """
    user = ctx.deps.sender
    pp = user.personality_prompts.get(name=name)
    return pp.name, pp.description, pp.prompt_template


@sync_to_async
def create_personality(
    ctx: RunContext[Dependency],
    name: str,
    description: str,
    prompt_template: str,
    use: bool = False,
):
    """Create a new personality prompt for the current user.

    Update any existing prompt with the same name.

    Use `{agent_name}` as a placeholder for the agent name in the prompt template.

    Args:
        name: The name of the personality prompt.
        description: The description of the personality prompt.
        prompt_template: The prompt template.
        use: Whether to set the new personality prompt as the current one.
    """
    user = ctx.deps.sender
    p = (
        user.personality_prompts.update_or_create(
            name=name,
            defaults={
                "description": description,
                "prompt_template": prompt_template,
            },
        )
    )[0]

    if use:
        user.prompt = p
        user.save()


@sync_to_async
def delete_personality(ctx: RunContext[Dependency], name: str):
    """Delete a personality of the agent of the current user.

    Args:
        name: The name of the personality to delete.
    """
    user = ctx.deps.sender
    user.personality_prompts.filter(name=name).delete()


@sync_to_async
def use_personality(ctx: RunContext[Dependency], name: str):
    """Set the personality of the agent of the current user.

    Args:
        name: The name of the personality to use.
    """
    user = ctx.deps.sender
    pp = user.personality_prompts.get(name=name)
    user.prompt = pp
    user.save()


@sync_to_async
def get_personality(
    ctx: RunContext[Dependency],
) -> tuple[str, str, str] | None:
    """Get the current personality of the agent for the current user.

    Returns:
        A tuple of (name, description, prompt_template) for the current personality,
        or None if no personality is set.
    """
    user = ctx.deps.sender
    pp = user.prompt
    if pp is None:
        return None
    return pp.name, pp.description, pp.prompt_template


prompt_toolset = FunctionToolset(
    [
        list_personalities,
        describe_personality,
        create_personality,
        delete_personality,
        use_personality,
        get_personality,
    ],
    id="camille.agent.personality",
)


@sync_to_async
def set_notes(ctx: RunContext[Dependency], notes: str):
    """Set your notes about the current user.

    Args:
        notes: The notes about the user.
    """
    user = ctx.deps.sender
    user.notes = notes
    user.save()


@sync_to_async
def append_to_notes(ctx: RunContext[Dependency], additional_notes: str):
    """Append to your notes about the current user.

    Args:
        additional_notes: The additional notes to append about the user.
    """
    user = ctx.deps.sender
    if user.notes:
        user.notes += "\n" + additional_notes
    else:
        user.notes = additional_notes

    user.save()


note_toolset = FunctionToolset(
    [
        # get_notes_for_current_user,
        set_notes,
        append_to_notes,
    ],
    id="camille.user.notes",
)

toolsets = [
    model_toolset,
    prompt_toolset,
    note_toolset,
]
