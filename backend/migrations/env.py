"""Alembic environment — async engine, auto-discover models, read config from .env."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.shared.database import Base

# Import all models so Alembic can discover them for autogenerate
import app.models  # noqa: F401

# Alembic Config
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Target metadata from our Base
target_metadata = Base.metadata

# Override sqlalchemy.url from settings (not hardcoded in alembic.ini)
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    """Generate SQL offline — no DB connection needed."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Execute migrations with the given connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations online using async engine."""
    connectable = create_async_engine(
        settings.database_url,
        echo=settings.debug,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
