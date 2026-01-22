from pydantic_ai import RunContext

from camille.ai.deps import Deps
from camille.ai.schemas import ProfileSchema
from camille.models import Profile


def personality_context(ctx: RunContext[Deps]) -> str:
    personality = ctx.deps.profile.personality
    if personality is None:
        return ""

    return personality.prompt_template.format(agent_name=ctx.deps.agent_name)


def thread_context(ctx: RunContext[Deps]) -> str:
    profile = ctx.deps.profile
    thread = ctx.deps.thread
    msg = f"The current conversation was started at {thread.created_at}.\n"
    if thread.summary:
        msg += f"The conversation summary is:\n\n{thread.summary}"
    else:
        msg += "There is no summary for this conversation."

    # List participants
    participants = set(Profile.objects.filter(llm_interaction__thread=thread))
    participants.add(profile)

    msg += f"\nParticipants in the conversation are:\n```json\n{[ProfileSchema.from_orm(p) for p in participants]}\n```"

    return msg


def user_profile_context(ctx: RunContext[Deps]) -> str:
    profile = ctx.deps.profile
    return f"The last message was sent by user: {profile.user.username} (profile ID: {profile.id})"
