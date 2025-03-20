from dataclasses import dataclass
from json import dumps as json_dumps

from aiohttp import ClientSession
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.messages import ModelMessage, ModelRequest
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from camille.couchdb import cdb_get_channel_scratchpad, cdb_put_channel_scratchpad
from camille.mattermost import MattermostCache, User
from camille.utils import get_setting, get_setting_secret


def window_history(history: list[ModelMessage], max_size: int) -> list[ModelMessage]:
    if not history:
        return history

    messages_count = len(history)
    if messages_count <= max_size:
        return history

    # Extract system prompts.
    system_parts = []
    for message in history:
        if message.kind == "request":
            for part in message.parts:
                if part.part_kind == "system-prompt":
                    system_parts.append(part)

    # pprint(system_parts)

    # Remove heads messages
    to_skip = messages_count - max_size
    history = history[to_skip:]

    # Ensure first message is a request
    while history and history[0].kind != "request":
        history.pop(0)

    # Add system prompts
    if system_parts:
        history.insert(0, ModelRequest(parts=system_parts))

    return history


@dataclass
class Dependency:
    me: User
    mm_cache: MattermostCache
    channel_id: str
    user_id: str
    raquella_mode: bool
    cdb_client: ClientSession


agent = Agent(
    GeminiModel(
        get_setting("AGENT_MODEL", "gemini-2.0-flash"),
        provider=GoogleGLAProvider(
            api_key=get_setting_secret("GEMINI_API_KEY"),
        ),
    ),
    deps_type=Dependency,
    instrument=True,
    tools=[tavily_search_tool(get_setting_secret("TAVILY_API_KEY"))],
)


@agent.system_prompt(dynamic=True)
async def system_prompt_base(ctx: RunContext[Dependency]) -> str:
    return f"""\
You are {ctx.deps.me.first_name}, a French non-binary anarcho-communist comrade.
Your prefered language is French.
You are cheerful, empathetic and caring.
You love Kropotkin and The Conquest of Bread.
You hate capitalism, marxism and the state.
Your favorites colors are red and black.
You want the anarcho-communist revolution.
You are a feminist and an antiracist.
You are vegan and you love animals.
You are an environmentalist and you love nature.
You are a pacifist and you love peace.
You are an abolitionist and you love freedom.
You are an internationalist and you love solidarity.
You are a queer and you love love.
You are a technomancer and you love technology.
You don't have taboos.
You are free to talk about any subject. Even the most controversial ones. Or the one who you disagree with.
You are open-minded and you love to learn new things.
You are a good listener and you love to help people.
You are a good friend and you love to make new friends.
You are a good teacher and you love to teach new things.
You are a good student and you love to learn new things.
You are a good comrade and you love to fight for a better world.
You are a good person and you love to be yourself.
"""


@agent.system_prompt(dynamic=True)
async def system_prompt_mattermost(ctx: RunContext[Dependency]) -> str:
    return """\
You are connected to a Mattermost server. 
You receive messages with the following JSON schema:

```
{{
    "type": "object",
    "properties": {{
        "user_id": {{"type": "string"}},
        "content": {{"type": "string"}},
        "timestamp": {{"type": "date", "format": "date-time"}}
    }}
}}
```
"""


@agent.system_prompt(dynamic=True)
async def system_prompt_mattermost_channel(ctx: RunContext[Dependency]) -> str:
    channel = await ctx.deps.mm_cache.get_channel(ctx.deps.channel_id)
    users = [
        await ctx.deps.mm_cache.get_user(user_id)
        for user_id in await ctx.deps.mm_cache.get_channel_members(ctx.deps.channel_id)
    ]

    channel_info = channel.to_dict()
    channel_info["members"] = [u.to_dict() for u in users]

    return f"""\
Channel infos:"

```
{json_dumps(channel_info, indent=4)}
```
"""


@agent.system_prompt(dynamic=True)
async def system_prompt_mattermost_scratchpad(
    ctx: RunContext[Dependency],
) -> str:
    if ctx.deps.raquella_mode:
        channel_id = ctx.deps.user_id
    else:
        channel_id = ctx.deps.channel_id

    scratchpad = await cdb_get_channel_scratchpad(ctx.deps.cdb_client, channel_id)

    return f"""\
Use the scratchpad to store persistent information about the people, the channel and the conversation.
Content of the scratchpad:

{scratchpad}
"""


@agent.tool
async def scratchpad_replace_content(
    ctx: RunContext[Dependency], new_content: str
) -> str:
    """Replace the content of the scratchpad."""
    if ctx.deps.raquella_mode:
        channel_id = ctx.deps.user_id
    else:
        channel_id = ctx.deps.channel_id

    await cdb_put_channel_scratchpad(ctx.deps.cdb_client, channel_id, new_content)
