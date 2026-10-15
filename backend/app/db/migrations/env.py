"""Alembic environment configuration for database migrations."""

from logging.config import fileConfig
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure backend root is in python path
backend_path = Path(__file__).resolve().parents[3]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from backend.app.config import settings
from backend.app.db.models import Base
from backend.app.db.session import get_engine_args, init_db_extensions

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return settings.database_url or "sqlite:///./modis_viirs.db"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        **get_engine_args(url),
    )

    # Initialize PostgreSQL PostGIS / pgcrypto extensions if connecting to PostgreSQL
    init_db_extensions(connectable)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
