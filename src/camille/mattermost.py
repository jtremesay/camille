from httpx import AsyncClient as HttpClient


class MattermostClient(HttpClient):
    def __init__(self, base_url: str, token: str):
        headers = {
            "Authorization": f"Bearer {token}",
        }
        super().__init__(base_url=base_url + "/api/v4", headers=headers)
