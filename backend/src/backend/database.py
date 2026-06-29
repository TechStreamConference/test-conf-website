from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from backend.config import SETTINGS

_ENGINE = create_async_engine(
    SETTINGS.async_database_url,
    echo=SETTINGS.database_echo,
    pool_pre_ping=True,
)

ASYNC_SESSION_FACTORY = async_sessionmaker(
    bind=_ENGINE,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with ASYNC_SESSION_FACTORY() as session:
        yield session
