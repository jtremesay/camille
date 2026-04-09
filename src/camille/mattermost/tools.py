from pydantic_ai import FunctionToolset, RunContext

from camille.mattermost.deps import Dependency


async def get_channel_notes(ctx: RunContext[Dependency]) -> str:
    """Get your notes about the current channel.

    Returns:
        The notes about the channel.
    """
    return ctx.deps.channel.notes


async def set_channel_notes(ctx: RunContext[Dependency], notes: str):
    """Set your notes about the current channel.

    Args:
        notes: The notes about the channel.
    """
    channel = ctx.deps.channel
    channel.notes = notes

    await channel.asave()


async def get_notes_for_user(ctx: RunContext[Dependency], user_id: str) -> str:
    """Get your notes about an user in the thread.

    Args:
        user_id: The ID of the user.

    Returns:
        The notes about the user.
    """
    user = ctx.deps.users[user_id]
    return user.notes


async def set_notes_for_user(
    ctx: RunContext[Dependency], user_id: str, notes: str
) -> None:
    """Set your notes about an user in the thread.

    Args:
        user_id: The ID of the user.
        notes: The notes about the user.
    """
    user = ctx.deps.users[user_id]
    user.notes = notes

    await user.asave()


toolset = FunctionToolset(
    [
        get_channel_notes,
        set_channel_notes,
        get_notes_for_user,
        set_notes_for_user,
    ],
    id="camille.mm.note",
)
