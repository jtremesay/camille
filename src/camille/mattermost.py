from datetime import datetime

from httpx import AsyncClient as HttpClient
from pydantic import BaseModel


class MMUser(BaseModel):
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


class MattermostClient(HttpClient):
    def __init__(self, base_url: str, token: str):
        headers = {
            "Authorization": f"Bearer {token}",
        }
        super().__init__(base_url=base_url + "/api/v4", headers=headers)

    async def get(self, url: str, **kwargs) -> dict:
        r = await super().get(url, **kwargs)
        r.raise_for_status()

        return r.json()

    async def get_user(self, user_id: str) -> MMUser:
        data = await self.get(f"/users/{user_id}")

        return MMUser.from_json(data)

    async def get_me(self) -> MMUser:
        return await self.get_user("me")
