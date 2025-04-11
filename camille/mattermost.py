from dataclasses import dataclass
from json import dumps as json_dumps
from json import loads as json_loads

from aiohttp import ClientSession

from camille.utils import get_setting, get_setting_secret

type ChannelId = str

KAKAIMOULOX_ID = "4cum8jkhzff57na6mgrq37syuh"
RAQUELLA_ID = "nhdhr7hb43gkxq9pzy5hzbq4cw"


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
