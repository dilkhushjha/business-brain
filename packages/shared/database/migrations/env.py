"""Alembic environment.

This file was missing entirely from the repo -- only packages/shared/database/
migrations/versions/*.py existed. Alembic requires env.py at script_location
to actually run anything; without it, `alembic upgrade head` fails at the
first step for every user, regardless of how many migration scripts exist
in versions/.
"""
from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import the app's models so Base.metadata is fully populated (needed for
# `alembic revision --autogenerate` to see every table; not required for
# `upgrade`/`downgrade` against the already-written scripts in versions/,
# but there's no reason for autogenerate to silently miss tables later).
from packages.shared.database import models  # noqa: F401
from packages.shared.database.session import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Prefer the application's own settings (which respects .env/
    environment overrides) over the static value in alembic.ini, so
    migrations always run against the same database the app itself would
    connect to -- falls back to alembic.ini's sqlalchemy.url if the
    app's settings can't be imported for some reason."""
    try:
        from apps.api.app.core.config import settings
        return settings.database_url
    except Exception:
        return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (emits SQL to stdout)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection -- the normal case."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
