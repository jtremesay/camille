from datetime import datetime
from typing import Optional

from httpx import AsyncClient
from httpx_ws import AsyncWebSocketSession, aconnect_ws
from pydantic import BaseModel, TypeAdapter


class Team(BaseModel):
    id: str
    name: str
    display_name: str

    create_at: datetime
    update_at: datetime
    delete_at: datetime


TeamList = TypeAdapter(list[Team])


class Channel(BaseModel):
    id: str
    team_id: str
    type: str
    name: str
    display_name: str
    header: str
    purpose: str

    create_at: datetime
    update_at: datetime
    delete_at: datetime


ChannelList = TypeAdapter(list[Channel])


class User(BaseModel):
    id: str
    username: str
    nickname: str
    first_name: str
    last_name: str

    create_at: datetime
    update_at: datetime
    delete_at: datetime


UserList = TypeAdapter(list[User])


class ChannelMember(BaseModel):
    channel_id: str
    user_id: str


ChannelMemberList = TypeAdapter(list[ChannelMember])


class ModelClient:
    base_url: str

    def __init__(self, http_client: AsyncClient) -> None:
        self._http_client = http_client

    async def _get(self, url: str):
        full_url = self.get_full_url(url)

        response = await self._http_client.get(full_url)
        response.raise_for_status()

        return response

    async def _post(self, url: str, json: dict):
        full_url = self.get_full_url(url)

        response = await self._http_client.post(full_url, json=json)
        response.raise_for_status()

        return response

    def get_base_url(self) -> str:
        return self.base_url

    def get_full_url(self, url: str) -> str:
        full_url = self.get_base_url()
        if url:
            full_url += "/" + url
        return full_url


class ChannelClient(ModelClient):
    base_url = "channels"

    async def get(self, channel_id: str) -> Channel:
        response = await self._get(channel_id)
        return Channel.model_validate_json(response.content)

    async def list_members(self, channel_id: str) -> list[ChannelMember]:
        response = await self._get(f"{channel_id}/members")
        response.raise_for_status()
        return ChannelMemberList.validate_json(response.content)


class UserClient(ModelClient):
    base_url = "users"

    async def list(self) -> list[User]:
        response = await self._get("")

        return UserList.validate_json(response.content)

    async def get(self, user_id: str) -> User:
        response = await self._get(user_id)

        return User.model_validate_json(response.content)

    async def get_me(self) -> User:
        return await self.get("me")

    async def get_teams(self, user_id: str) -> list[Team]:
        response = await self._get(f"{user_id}/teams")
        response.raise_for_status()

        return TeamList.validate_json(response.content)

    async def get_channels_for_user(self, user_id: str, team_id: str) -> list[Channel]:
        response = await self._get(f"{user_id}/teams/{team_id}/channels")
        response.raise_for_status()

        return ChannelList.validate_json(response.content)


class PostClient(ModelClient):
    base_url = "posts"

    async def post(self, channel_id: str, message: str, root_id: Optional[str] = None):
        response = await self._post(
            "",
            json={"channel_id": channel_id, "root_id": root_id, "message": message},
        )
        response.raise_for_status()


class FileClient(ModelClient):
    base_url = "files"

    async def get_file(self, file_id: str) -> bytes:
        response = await self._get(file_id)
        response.raise_for_status()

        return response.content


class WebSocketClient:
    def __init__(self, http_client: AsyncClient):
        self._http_client = http_client
        self._ws_client: Optional[AsyncWebSocketSession] = None
        self.current_seq = 0

    async def connect(self, timeout: Optional[float] = None):
        async with aconnect_ws(
            "websocket",
            self._http_client,
        ) as ws:
            self._ws_client = ws
            while True:
                try:
                    event = await self._ws_client.receive_json(timeout=timeout)
                except TimeoutError:
                    yield "timeout", None, None, None
                    continue

                kind = event.get("event")
                if not kind:
                    continue

                if kind in {"status_change", "typing"}:
                    continue

                data = event["data"]
                broadcast = event.get("broadcast")
                seq = event["seq"]
                self.current_seq = max(self.current_seq, seq)

                yield kind, data, broadcast, seq

    async def on_event(self, kind: str, data, broadcast, seq):
        if event_handler := getattr(self, f"on_{kind}", None):
            print(
                f"Handling event: {kind}, Data: {data}, Broadcast: {broadcast}, Seq: {seq}"
            )
            await event_handler(data, broadcast, seq)
        else:
            print(
                f"Unhandled event: {kind}, Data: {data}, Broadcast: {broadcast}, Seq: {seq}"
            )

    async def send(self, action: str, data: dict) -> None:
        assert self._ws_client is not None

        self.current_seq += 1
        await self._ws_client.send_json(
            {
                "action": action,
                "data": data,
                "seq": self.current_seq,
            }
        )

    async def user_typing(self, channel_id: str) -> None:
        await self.send("user_typing", {"channel_id": channel_id})


class Mattermost:
    def __init__(
        self,
        base_url: str,
        api_token: str,
    ):
        self._http_client = AsyncClient(
            base_url=base_url + "/api/v4/",
            headers={
                "Authorization": f"Bearer {api_token}",
                "User-Agent": "CamilleBot/1.0",
            },
        )

        self.users = UserClient(self._http_client)
        self.channels = ChannelClient(self._http_client)
        self.posts = PostClient(self._http_client)
        self.files = FileClient(self._http_client)
        self.ws = WebSocketClient(self._http_client)

    async def __aenter__(self):
        await self._http_client.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.__aexit__(exc_type, exc_val, exc_tb)
