from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


settings = get_settings()

if settings.database_url.startswith("sqlite"):
    database_path = make_url(settings.database_url).database
    if database_path and database_path != ":memory:":
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
