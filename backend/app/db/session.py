# Configures the SQLAlchemy engine and session factory for Neon PostgreSQL.

import logging
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine setup
# ---------------------------------------------------------------------------
# Neon do tarah ke connections deta hai:
#   1. Pooled endpoint   — normal app requests ke liye (port 5432 on pooler host)
#   2. Direct endpoint   — Alembic migrations ke liye recommended
#
# Pooled connection mein transaction-mode pooling hota hai, isliye prepared
# statements ke liye compatibility=True banana padta hai.
#
# SQLAlchemy engine database connections ko manage karta hai,
# isliye har API request ke liye naya connection nahi banta.

def _build_database_url(raw_url: str) -> str:
    """Normalize postgresql:// to postgresql+psycopg:// for psycopg 3."""
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    return raw_url


def _create_engine():
    db_url = settings.DATABASE_URL
    if not db_url:
        logger.warning(
            "DATABASE_URL is not configured. "
            "Database-dependent endpoints will be unavailable."
        )
        return None

    normalized_url = _build_database_url(db_url)

    return create_engine(
        normalized_url,
        # Small pool suitable for a development monolith.
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,     # connection validity check karta hai before use
        pool_timeout=30,
        connect_args={
            # Neon pooled mode mein prepared statements disable karna padta hai.
            "prepare_threshold": None,
        },
    )


engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed after each request."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """Execute a lightweight query. Returns True if the database responds."""
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        # Sirf error log karo — connection string ya credentials mat dikhao.
        logger.warning("Database health check failed: %s", type(exc).__name__)
        return False
