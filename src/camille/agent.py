from typing import Optional, cast

from sqlalchemy import Engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from mattermost.client import MattermostClient

from .models import MMUser


class Agent:
    def __init__(self, mm_client: MattermostClient, db_engine: AsyncEngine):
        self.mm_client = mm_client
        self.db_engine = db_engine
        async_session = sessionmaker(
            cast(Engine, self.db_engine),
            expire_on_commit=False,
            class_=AsyncSession,
        )
        self.db_session: AsyncSession = cast(AsyncSession, async_session())

        self.me: Optional[MMUser] = None

    async def __aenter__(self):
        await self.mm_client.__aenter__()
        await self.db_session.__aenter__()

        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.mm_client.__aexit__(exc_type, exc, tb)
        await self.db_session.__aexit__(exc_type, exc, tb)
        await self.db_engine.dispose()

    async def run(self):
        mm_me = await self.mm_client.users.get_me()

        # Update or insert the current user
        async with self.db_session.begin():
            try:
                me = (
                    await self.db_session.execute(
                        select(MMUser).where(MMUser.mm_id == mm_me.id)
                    )
                ).scalar_one()
            except NoResultFound:
                me = MMUser(
                    mm_id=mm_me.id,
                    created_at=mm_me.created_at,
                    update_at=mm_me.update_at,
                    delete_at=mm_me.delete_at,
                    username=mm_me.username,
                    nickname=mm_me.nickname,
                    first_name=mm_me.first_name,
                    last_name=mm_me.last_name,
                )
                self.db_session.add(me)

        self.me = me
