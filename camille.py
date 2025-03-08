#!/usr/bin/env python3
from asyncio import run
from dataclasses import dataclass
from datetime import datetime, timezone
from json import dumps as json_dumps
from json import loads as json_loads
from os import environ
from typing import Optional

import logfire
from aiohttp import ClientSession, WSMsgType
from pydantic_ai import Agent, RunContext
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter, ModelRequest
from pydantic_ai.models.gemini import (
    GeminiModel,
    GeminiModelSettings,
    GeminiSafetySettings,
)
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_core import to_jsonable_python

##############################################################################
# Settings
##############################################################################


def get_setting(key: str, *args):
    try:
        return environ[key]
    except KeyError:
        try:
            return args[0]
        except IndexError:
            raise KeyError(f"{key} must be set")


def get_setting_secret(key: str, *args):
    try:
        secret_file = environ[key + "_FILE"]
    except KeyError:
        return get_setting(key, *args)
    else:
        with open(secret_file) as f:
            return f.read().strip()


###############################################################################
# Mattermost
##############################################################################

type ChannelId = str


@dataclass
class Channel:
    id: ChannelId
    name: str
    display_name: str
    header: str
    purpose: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            name=data["name"],
            display_name=data["display_name"],
            header=data["header"],
            purpose=data["purpose"],
        )

    @classmethod
    def from_json(cls, data: str):
        return cls.from_dict(json_loads(data))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "header": self.header,
            "purpose": self.purpose,
        }

    def to_json(self):
        return json_dumps(self.to_dict())


type UserId = str


@dataclass
class User:
    id: UserId
    username: str
    nickname: str
    first_name: str
    last_name: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            username=data["username"],
            nickname=data["nickname"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )

    @classmethod
    def from_json(cls, data: str):
        return cls.from_dict(json_loads(data))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

    def to_json(self):
        return json_dumps(self.to_dict())


def mm_get_client() -> ClientSession:
    return ClientSession(
        get_setting("MATTERMOST_HOST"),
        headers={
            "Authorization": "Bearer " + get_setting_secret("MATTERMOST_API_TOKEN")
        },
    )


async def mm_get_user(mm_client: ClientSession, user_id: UserId) -> User:
    r = await mm_client.get(f"/api/v4/users/{user_id}")
    data = await r.json()

    return User.from_dict(data)


async def mm_get_channel(mm_client: ClientSession, channel_id: ChannelId) -> Channel:
    r = await mm_client.get(f"/api/v4/channels/{channel_id}")
    data = await r.json()

    return Channel.from_dict(data)


async def mm_get_channel_members(
    mm_client: ClientSession, channel_id: ChannelId
) -> set[UserId]:
    r = await mm_client.get(f"/api/v4/channels/{channel_id}/members")
    data = await r.json()

    return {m["user_id"] for m in data}


async def mm_post_message(
    mm_client: ClientSession, channel_id: ChannelId, message: str
) -> None:
    r = await mm_client.post(
        f"/api/v4/posts", json={"channel_id": channel_id, "message": message}
    )
    await r.json()


class MattermostCache:
    def __init__(self, client: ClientSession):
        self.client = client
        self.users: dict[UserId, User] = {}
        self.channels: dict[ChannelId, Channel] = {}
        self.channel_members: dict[ChannelId, set[UserId]] = {}

    async def get_me(self) -> User:
        return await self.get_user("me")

    async def get_user(self, user_id: UserId) -> User:
        try:
            return self.users[user_id]
        except KeyError:
            user = await mm_get_user(self.client, user_id)
            self.users[user_id] = user
            return user

    async def get_channel(self, channel_id: ChannelId) -> Channel:
        try:
            return self.channels[channel_id]
        except KeyError:
            channel = await mm_get_channel(self.client, channel_id)
            self.channels[channel_id] = channel
            return channel

    async def get_channel_members(self, channel_id: ChannelId) -> set[UserId]:
        try:
            return self.channel_members[channel_id]
        except KeyError:
            channel_members = await mm_get_channel_members(self.client, channel_id)
            self.channel_members[channel_id] = channel_members
            return channel_members

    async def add_channel_member(self, channel_id: ChannelId, user_id: UserId) -> None:
        try:
            self.channel_members[channel_id].add(user_id)
        except KeyError:
            await self.get_channel_members(channel_id)

    async def remove_channel_member(
        self, channel_id: ChannelId, user_id: UserId
    ) -> None:
        try:
            self.channel_members[channel_id].remove(user_id)
        except KeyError:
            await self.get_channel_members(channel_id)


##############################################################################
# CouchDB
##############################################################################


def cdb_get_client() -> ClientSession:
    return ClientSession(get_setting_secret("COUCHDB_URL"))


async def cdb_get_history(
    cdb_client: ClientSession, channel_id: ChannelId
) -> tuple[Optional[str], Optional[list[ModelMessage]]]:
    r = await cdb_client.get(f"channel_{channel_id}")
    if r.status == 404:
        return None, None
    r.raise_for_status()

    rev = r.headers["etag"][1:-1]
    history = (await r.json()).get("history")
    if not history:
        return rev, None

    history = ModelMessagesTypeAdapter.validate_python(history)

    return rev, history


async def cdb_put_history(
    cdb_client: ClientSession,
    channel_id: ChannelId,
    revision: Optional[str],
    history: list[ModelMessage],
) -> None:
    params = {}
    if revision is not None:
        params["rev"] = revision
    json = {"history": to_jsonable_python(history)}

    r = await cdb_client.put(
        f"channel_{channel_id}",
        params=params,
        json=json,
    )
    r.raise_for_status()


##############################################################################
# Agent
##############################################################################


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


###############################################################################
# Main
###############################################################################


async def amain() -> None:
    logfire.configure(
        token=get_setting_secret("LOGFIRE_TOKEN", None),
        send_to_logfire="if-token-present",
        environment=get_setting("ENVIRONMENT"),
        service_name="camille",
    )
    logfire.instrument_httpx(capture_all=True)
    logfire.instrument_aiohttp_client()

    window_size = int(get_setting("WINDOW_SIZE", 1024))
    settings = GeminiModelSettings(
        gemini_safety_settings=[
            GeminiSafetySettings(
                category=category,
                threshold="BLOCK_NONE",
            )
            for category in [
                # "HARM_CATEGORY_UNSPECIFIED",
                "HARM_CATEGORY_HARASSMENT",
                "HARM_CATEGORY_HATE_SPEECH",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "HARM_CATEGORY_DANGEROUS_CONTENT",
                "HARM_CATEGORY_CIVIC_INTEGRITY",
            ]
        ]
    )

    async with cdb_get_client() as cdb_client:
        async with mm_get_client() as mm_client:
            mm_cache = MattermostCache(mm_client)
            me = await mm_cache.get_me()

            seq = 0
            async with mm_client.ws_connect("/api/v4/websocket") as ws:
                async for ws_message in ws:
                    # Ignore non-text WS messages
                    if ws_message.type != WSMsgType.TEXT:
                        continue

                    ws_data = ws_message.json()
                    mm_event = ws_data.get("event")
                    if not mm_event:
                        continue
                    # logfire.info(
                    #     "event received {event=}", event=mm_event, data=ws_data
                    # )

                    mm_event_data = ws_data["data"]
                    seq = max(seq, ws_data["seq"])

                    # Ignore non-post MM events
                    if mm_event != "posted":
                        match mm_event:
                            case "user_updated":
                                user = User.from_dict(mm_event_data["user"])
                                mm_cache.users[user.id] = user
                            case "channel_updated":
                                channel = Channel.from_json(mm_event_data["channel"])
                                mm_cache.channels[channel.id] = channel
                            case "user_added":
                                user_id = mm_event_data["user_id"]
                                channel_id = ws_data["broadcast"]["channel_id"]
                                await mm_cache.add_channel_member(channel_id, user_id)
                            case "user_removed":
                                user_id = mm_event_data.get("user_id")
                                if user_id:
                                    channel_id = ws_data["broadcast"]["channel_id"]
                                    await mm_cache.remove_channel_member(
                                        channel_id, user_id
                                    )

                        continue

                    post_data = json_loads(mm_event_data["post"])

                    # Ignore self messages
                    if post_data["user_id"] == me.id:
                        continue

                    # Ignore thread replies
                    if post_data["root_id"]:
                        continue

                    logfire.info("post received", data=post_data)
                    channel_id = post_data["channel_id"]

                    try:
                        seq += 1
                        await ws.send_json(
                            {
                                "action": "user_typing",
                                "seq": seq,
                                "data": {
                                    "channel_id": channel_id,
                                },
                            }
                        )

                        deps = Dependency(
                            mm_cache=mm_cache,
                            me=me,
                            channel_id=channel_id,
                        )

                        message = {
                            "user_id": post_data["user_id"],
                            "content": post_data["message"],
                            "timestamp": datetime.fromtimestamp(
                                post_data["create_at"] / 1000, tz=timezone.utc
                            ).isoformat(),
                        }

                        rev, history = await cdb_get_history(cdb_client, channel_id)
                        history = window_history(history, window_size)
                        async with agent.iter(
                            json_dumps(message),
                            deps=deps,
                            message_history=history,
                            model_settings=settings,
                        ) as r:
                            async for node in r:
                                if agent.is_call_tools_node(node):
                                    for part in node.model_response.parts:
                                        if part.part_kind == "text":
                                            await mm_post_message(
                                                mm_client,
                                                channel_id,
                                                part.content,
                                            )

                            # history = r.result.all_messages()
                            await cdb_put_history(
                                cdb_client, channel_id, rev, r.result.all_messages()
                            )
                    except Exception as e:
                        logfire.exception("error")
                        await mm_post_message(
                            mm_client,
                            post_data["channel_id"],
                            f"Error: {e}",
                        )


def main():
    run(amain())


if __name__ == "__main__":
    main()
