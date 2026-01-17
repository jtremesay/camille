from json import dumps as json_dumps

from httpx import AsyncClient
from pydantic_ai import FunctionToolset, RunContext

from camille.mattermost.deps import Dependency
from camille.models import MMChannel


def mm_system_prompt(ctx: RunContext[Dependency]) -> str:
    return f"""\
You are connected to a Mattermost server.

Details of the current channel:
```json
{
        json_dumps(
            dict(
                id=ctx.deps.channel.id,
                type=MMChannel.Type(ctx.deps.channel.type).label,
                name=ctx.deps.channel.name,
                display_name=ctx.deps.channel.display_name,
                header=ctx.deps.channel.header,
                purpose=ctx.deps.channel.purpose,
                notes=ctx.deps.channel.notes,
            ),
            indent=2,
        )
    }
```

Users present in the channel:
```json
{
        json_dumps(
            [
                dict(
                    id=user.id,
                    username=user.username,
                    nickname=user.nickname,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    notes=user.notes,
                )
                for user in ctx.deps.users.values()
            ],
            indent=2,
        )
    }
```

You can only see the messages of the current thread.
The notes store information about the channel and the users that are shared between the threads.
Update the notes of the channel and the users with the information you have so you can use them in the future.
"""


async def update_channel_notes(ctx: RunContext[Dependency], notes: str):
    """Update your notes about the current channel.

    Args:
        notes: The new notes about the channel.
    """
    channel = ctx.deps.channel
    channel.notes = notes
    await channel.asave()


async def update_user_notes(ctx: RunContext[Dependency], user_id: str, notes: str):
    """Update your notes about an user.

    Args:
        user_id: The ID of the user.
        notes: The new notes about the user.
    """
    user = ctx.deps.users[user_id]
    user.notes = notes
    await user.asave()


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


toolset = FunctionToolset(
    [
        update_channel_notes,
        update_user_notes,
        get_url_content,
    ]
)
