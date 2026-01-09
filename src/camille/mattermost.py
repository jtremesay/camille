from datetime import datetime
from typing import cast

from httpx import AsyncClient as HttpClient
from pydantic import BaseModel


class MMObject(BaseModel):
    @classmethod
    def from_json(cls, data: dict) -> "MMObject":
        return cls(**data)


class MMUser(MMObject):
    id: str
    created_at: datetime
    update_at: datetime
    delete_at: datetime
    username: str
    nickname: str
    first_name: str
    last_name: str

    @classmethod
    def from_json(cls, data: dict) -> "MMUser":
        return cls(
            id=data["id"],
            created_at=datetime.fromtimestamp(data["create_at"] / 1000),
            update_at=datetime.fromtimestamp(data["update_at"] / 1000),
            delete_at=datetime.fromtimestamp(data["delete_at"] / 1000),
            username=data["username"],
            nickname=data["nickname"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )


class MMObjectClient:
    obj_class: type[MMObject]
    name: str

    def __init__(self, client: "MattermostClient"):
        self.client = client

    async def get(self, object_id: str) -> MMObject:
        data = await self.client.get(f"/{self.name}s/{object_id}")
        return self.obj_class.from_json(data)


class MMUserClient(MMObjectClient):
    obj_class = MMUser
    name = "user"

    async def get_me(self) -> MMUser:
        return cast(MMUser, await self.get("me"))


class MattermostClient:
    def __init__(self, base_url: str, token: str):
        headers = {
            "Authorization": f"Bearer {token}",
        }
        self.http_client = HttpClient(base_url=base_url + "/api/v4", headers=headers)
        self.users = MMUserClient(self)

    async def __aenter__(self) -> "MattermostClient":
        await self.http_client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.http_client.__aexit__(exc_type, exc, tb)

    async def get(self, url: str, **kwargs) -> dict:
        r = await self.http_client.get(url, **kwargs)
        r.raise_for_status()

        return r.json()
