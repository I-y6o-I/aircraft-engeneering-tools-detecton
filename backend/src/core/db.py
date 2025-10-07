import asyncio
from typing import AsyncGenerator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from .settings import settings

# Declarative Base
class Base(DeclarativeBase):
    """SQLAlchemy Declarative Base used by models."""
    pass

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Create or return a singleton async engine if DATABASE_URL is set."""

    global _engine, _session_factory
    if _engine is None:
        if not settings.DATABASE_URL:
            # No DB configured; create a dummy engine to avoid crashes if imported
            raise RuntimeError("DATABASE_URL is not set. Configure it to use the database.")
        _engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields AsyncSession. Requires DATABASE_URL configured."""

    global _session_factory
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        yield session


async def ping_db() -> bool:
    """Simple ping for healthcheck: returns True if DB responds to SELECT 1."""

    if not settings.DATABASE_URL:
        return False
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False