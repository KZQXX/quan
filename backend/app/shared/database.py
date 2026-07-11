"""Async SQLAlchemy engine, session factory, and FastAPI dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ─── Engine ───────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.db_pool_size,
    pool_pre_ping=True,           # verify connections before use
    connect_args={                # SQLite-specific: allow multi-threaded access
        "check_same_thread": False,
    } if "sqlite" in settings.database_url else {},
)

# ─── Session Factory ──────────────────────────────────────────────────────

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,       # keep objects usable after commit
    autoflush=False,              # we control flush explicitly
)


# ─── Declarative Base ─────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base. All models inherit from this."""
    pass


# ─── FastAPI Dependency ───────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session, auto-close on request completion.

    Usage:
        @app.get("/pets")
        async def list_pets(db: AsyncSession = Depends(get_db)): ...
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
