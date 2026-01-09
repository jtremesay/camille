from asyncio import run

from camille import settings
from camille.mattermost.client.client import MattermostClient


async def amain():
    async with MattermostClient(
        base_url=settings.MATTERMOST_URL, token=settings.MATTERMOST_TOKEN
    ) as client:
        me = await client.users.get_me()
        print(me)
        # print(f"Logged in as: {me.username} ({me.first_name} {me.last_name})")


def main():
    run(amain())
