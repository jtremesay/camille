from typing import Optional

from aiohttp import ClientSession
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python

from camille.mattermost import ChannelId
from camille.utils import get_setting_secret


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


async def cdb_get_channel_scratchpad(
    cdb_client: ClientSession, channel_id: ChannelId
) -> str:
    r = await cdb_client.get(f"channel_{channel_id}_scratchpad")
    if r.status == 404:
        return ""
    r.raise_for_status()

    return (await r.json())["scratchpad"]


async def cdb_put_channel_scratchpad(
    cdb_client: ClientSession, channel_id: ChannelId, scratchpad: str
) -> None:
    scratchpad_id = f"channel_{channel_id}_scratchpad"
    r = await cdb_client.head(scratchpad_id)
    if r.status == 404:
        params = {}
    else:
        params = {"rev": r.headers["etag"][1:-1]}

    r = await cdb_client.put(
        f"channel_{channel_id}_scratchpad",
        params=params,
        json={"scratchpad": scratchpad},
    )
    r.raise_for_status()
