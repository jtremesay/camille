from asyncio import run
from os import environ

from mattermost.client import MattermostClient


async def amain():
    mm_url = environ["CAMILLE_MATTERMOST_URL"]
    mm_token = environ["CAMILLE_MATTERMOST_TOKEN"]

    async with MattermostClient(base_url=mm_url, token=mm_token) as client:
        me = await client.users.get_me()
        print(me)
        # print(f"Logged in as: {me.username} ({me.first_name} {me.last_name})")


def main():
    run(amain())
