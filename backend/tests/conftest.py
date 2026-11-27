# Test configuration and fixtures shared across all test modules.

import os
import uuid
import pytest

# Tests ke liye dummy JWT secret set karo — real secret expose nahi karte.
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests-only-32chars!")
os.environ.update({
    "EMBEDDING_PROVIDER": "jina",
    "JINA_API_KEY": "test-jina-api-key",
    "EMBEDDING_MODEL": "jina-embeddings-v3",
    "EMBEDDING_DIMENSION": "1024",
    "EMBEDDING_BATCH_SIZE": "16",
})
os.environ.setdefault("DATABASE_URL", "")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# ---------------------------------------------------------------------------
# In-memory test helpers (no real DB needed for unit tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    """TestClient without a real database — for unit tests only."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
