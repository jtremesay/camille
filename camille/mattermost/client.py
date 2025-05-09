from os import environ
from typing import Optional

from django.conf import settings
from httpx import AsyncClient
from httpx_ws import AsyncWebSocketSession, aconnect_ws
from pydantic import BaseModel, TypeAdapter


class Team(BaseModel):
    id: str
    name: str
    display_name: str


TeamList = TypeAdapter(list[Team])


class Channel(BaseModel):
    id: str
    type: str
    name: str
    display_name: str
    header: str
    purpose: str


ChannelList = TypeAdapter(list[Channel])


class User(BaseModel):
    id: str
    username: str
    nickname: str
    first_name: str
    last_name: str


UserList = TypeAdapter(list[User])


class ChannelMember(BaseModel):
    channel_id: str
    user_id: str


ChannelMemberList = TypeAdapter(list[ChannelMember])


class Mattermost:
    def __init__(
        self,
        base_url: str,
        token: str,
    ):
        self._http_client = AsyncClient(
            base_url=base_url + "/api/v4/", headers={"Authorization": f"Bearer {token}"}
        )
        self._ws_client: Optional[AsyncWebSocketSession] = None
        self.current_seq = 0

    @classmethod
    def create(cls):
        return cls(settings.MATTERMOST_HOST, settings.MATTERMOST_API_TOKEN)

    async def __aenter__(self):
        await self._http_client.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._http_client.__aexit__(exc_type, exc_val, exc_tb)

    async def connect(
        self,
    ):
        async with aconnect_ws("websocket", self._http_client) as ws:
            self._ws_client = ws
            while True:
                event = await self._ws_client.receive_json()
                kind = event.get("event")
                if not kind:
                    continue
                data = event["data"]
                broadcast = event.get("broadcast")
                seq = event["seq"]
                self.current_seq = max(self.current_seq, seq)

                await self.on_event(kind, data, broadcast, seq)

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

    async def get_users(self) -> list[User]:
        response = await self._http_client.get(f"users")
        response.raise_for_status()
        return UserList.validate_json(response.content)

    async def get_user(self, user_id: str) -> User:
        response = await self._http_client.get(f"users/{user_id}")
        response.raise_for_status()
        return User.model_validate_json(response.content)

    async def get_me(self) -> User:
        return await self.get_user("me")

    async def get_teams(self, user_id: str) -> list[Team]:
        response = await self._http_client.get(f"users/{user_id}/teams")
        response.raise_for_status()
        return TeamList.validate_json(response.content)

    async def get_channels_for_user(self, user_id: str, team_id: str) -> list[Channel]:
        response = await self._http_client.get(
            f"users/{user_id}/teams/{team_id}/channels"
        )
        response.raise_for_status()
        return ChannelList.validate_json(response.content)

    async def get_channel(self, channel_id: str) -> Channel:
        response = await self._http_client.get(f"channels/{channel_id}")
        response.raise_for_status()
        return Channel.model_validate_json(response.content)

    async def get_channel_members(self, channel_id: str) -> list[ChannelMember]:
        response = await self._http_client.get(f"channels/{channel_id}/members")
        response.raise_for_status()
        return ChannelMemberList.validate_json(response.content)

    async def post_message(self, channel_id: str, root_id: str, message: str):
        response = await self._http_client.post(
            f"posts",
            json={"channel_id": channel_id, "root_id": root_id, "message": message},
        )
        response.raise_for_status()

    async def get_file(self, file_id: str) -> bytes:
        response = await self._http_client.get(f"files/{file_id}")
        response.raise_for_status()
        return response.content

    async def ws_send(self, action: str, data: dict) -> None:
        self.current_seq += 1
        await self._ws_client.send_json(
            {
                "action": action,
                "data": data,
                "seq": self.current_seq,
            }
        )

    async def user_typing(self, channel_id: str) -> None:
        await self.ws_send("user_typing", {"channel_id": channel_id})
