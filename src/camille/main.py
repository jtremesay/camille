from asyncio import run

from camille import settings
from camille.mattermost import MattermostClient


async def amain():
    async with MattermostClient(
        base_url=settings.MATTERMOST_URL, token=settings.MATTERMOST_TOKEN
    ) as client:
        response = await client.get("/users/me")
        print(response.json())


def main():
    run(amain())
