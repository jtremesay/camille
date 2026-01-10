from asyncio import run
from os import environ

from sqlalchemy.ext.asyncio import create_async_engine

from mattermost.client import MattermostClient

from .agent import Agent


async def amain():
    mm_url = environ["CAMILLE_MATTERMOST_URL"]
    mm_token = environ["CAMILLE_MATTERMOST_TOKEN"]
    db_url = "sqlite+aiosqlite:///db.sqlite3"

    async with Agent(
        MattermostClient(mm_url, mm_token), create_async_engine(db_url, echo=True)
    ) as agent:
        await agent.run()
        print("Current user:", agent.me.username)


def main():
    run(amain())
