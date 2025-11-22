"""Alembic environment configuration."""
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import your models here
from app.infrastructure.database.base import Base
from app.models import UserModel  # Import all models
from app.core.config import settings

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata

# Use DIRECT_URL if available (bypasses pgBouncer), otherwise use DATABASE_URL
database_url = str(settings.DIRECT_URL) if settings.DIRECT_URL else str(settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", database_url)



def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the provided connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    configuration = config.get_section(config.config_ini_section, {})
    
    # Use DIRECT_URL to bypass pgBouncer
    database_url = str(settings.DIRECT_URL) if settings.DIRECT_URL else str(settings.DATABASE_URL)
    configuration["sqlalchemy.url"] = database_url
    
    # Check if using pgBouncer and configure statement cache accordingly
    connect_args = {}
    if "pooler" in database_url.lower() or "pgbouncer" in database_url.lower():
        connect_args["statement_cache_size"] = 0
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
