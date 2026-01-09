from asyncio import run
from os import environ

from sqlalchemy.ext.asyncio import create_async_engine

from mattermost.client import MattermostClient

from .models import meta


async def amain():
    engine = None
    try:
        engine = create_async_engine(
            "sqlite+aiosqlite:///db.sqlite",
            echo=True,
        )
        async with engine.begin() as conn:
            await conn.run_sync(meta.drop_all)
            await conn.run_sync(meta.create_all)
    finally:
        if engine is not None:
            await engine.dispose()

    mm_url = environ["CAMILLE_MATTERMOST_URL"]
    mm_token = environ["CAMILLE_MATTERMOST_TOKEN"]

    async with MattermostClient(base_url=mm_url, token=mm_token) as client:
        me = await client.users.get_me()
        print(me)
        # print(f"Logged in as: {me.username} ({me.first_name} {me.last_name})")


def main():
    run(amain())
