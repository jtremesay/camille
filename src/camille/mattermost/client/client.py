from httpx import AsyncClient as HttpClient

from .user import MMUserClient


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
