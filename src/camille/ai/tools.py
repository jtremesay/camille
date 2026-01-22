from typing import Optional

from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset

from camille.ai.deps import Deps
from camille.ai.schemas import AgentPersonalitySchema
from camille.models import AgentPersonality


def update_notes_for_user(ctx: RunContext[Deps], new_notes: str) -> None:
    """
    Update the notes for current user.

    :param new_notes: The new notes to set for the user.
    """
    profile = ctx.deps.profile
    profile.notes = new_notes
    profile.save()


def set_model_name_for_user(ctx: RunContext[Deps], model_name: str) -> None:
    """
    Set the llm model name for current user.

    :param model_name: The new model name to set for the user.
    """
    profile = ctx.deps.profile
    profile.model_name = model_name
    profile.save()


def list_personalities(ctx: RunContext[Deps]) -> list[AgentPersonalitySchema]:
    """
    List available personalities.

    :return: A list of personalities.
    """

    personalities = AgentPersonality.objects.all()
    return [AgentPersonalitySchema.from_orm(p) for p in personalities]


def set_personality_for_user(
    ctx: RunContext[Deps], personality_id: Optional[int] = None
) -> None:
    """
    Set the personality for current user.

    :param personality_id: The personality ID to set for the user.
    """
    if personality_id is not None:
        personality = AgentPersonality.objects.get(id=personality_id)
    else:
        personality = None

    profile = ctx.deps.profile
    profile.personality = personality
    profile.save()


def create_personality_for_user(
    ctx: RunContext[Deps], name: str, description: str, prompt_template: str
) -> None:
    """
    Create a new personality for current user.

    Recognized tags in prompt_template:
     - `{agent_name}`: The name of the agent.

    :param name: The name of the new personality.
    :param description: The description of the new personality.
    :param prompt_template: The prompt template of the new personality.
    """
    AgentPersonality.objects.create(
        name=name,
        description=description,
        prompt_template=prompt_template,
    )


user_toolset = FunctionToolset(
    id="camille_user_tools",
    tools=[
        update_notes_for_user,
        set_model_name_for_user,
        list_personalities,
        set_personality_for_user,
        create_personality_for_user,
    ],
)


def set_thread_summary(ctx: RunContext[Deps], summary: str) -> None:
    """
    Set the summary for the current LLM thread.

    :param summary: The summary to set for the thread.
    """
    thread = ctx.deps.thread
    thread.summary = summary
    thread.save()


thread_toolset = FunctionToolset(
    id="camille_thread_tools",
    tools=[
        set_thread_summary,
    ],
)
