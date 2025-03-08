from asyncio import run
from datetime import datetime, timezone
from json import dumps as json_dumps
from json import loads as json_loads

import logfire
from aiohttp import WSMsgType
from pydantic_ai.models.gemini import GeminiModelSettings, GeminiSafetySettings

from camille.agent import Dependency, agent, window_history
from camille.couchdb import cdb_get_client, cdb_get_history, cdb_put_history
from camille.mattermost import (
    Channel,
    MattermostCache,
    User,
    mm_get_client,
    mm_post_message,
)
from camille.utils import get_setting, get_setting_secret


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
