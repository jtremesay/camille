from sqlalchemy.ext.asyncio.engine import AsyncEngine, create_async_engine


def create_db_engine(url: str) -> AsyncEngine:
    connect_args = {"check_same_thread": False}

    return create_async_engine(url, connect_args=connect_args)
