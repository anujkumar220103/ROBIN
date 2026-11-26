# Alembic environment configuration — connects migrations to SQLAlchemy models.

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Backend source directory ko Python path mein add karo
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.db.base import Base

# ORM models load karne ke liye import karna padta hai —
# warna Alembic tables detect nahi karta.
import app.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_migration_url() -> str:
    """Return the database URL for migrations.

    Migration ke liye direct connection prefer karte hain —
    Neon pooler mein kuch migration commands compatible nahi hote.
    """
    raw = settings.migration_database_url
    if not raw:
        raise RuntimeError(
            "DATABASE_URL or DATABASE_DIRECT_URL is not configured. "
            "Set it in backend/.env before running migrations."
        )
    # Normalize to psycopg driver
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg://", 1)
    return raw


def run_migrations_offline() -> None:
    """Run migrations without an active database connection."""
    url = _get_migration_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _get_migration_url()

    # Prepared statements disable karte hain — Neon pooler compatibility ke liye.
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"prepare_threshold": None},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
