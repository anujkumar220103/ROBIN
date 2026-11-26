# Loads and validates all application configuration from environment variables.
# Pydantic Settings automatically reads values from the .env file.

import json
from pathlib import Path
from typing import List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "ROBIN AI"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    # Neon ka pooled connection URL — normal app requests ke liye use hota hai.
    DATABASE_URL: str = ""
    # Direct (non-pooled) URL — Alembic migrations ke liye better hai.
    # Agar set nahi hai to DATABASE_URL se fallback kar lete hain.
    DATABASE_DIRECT_URL: str = ""

    # --- JWT ---
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Cookie ---
    AUTH_COOKIE_NAME: str = "robin_access_token"
    CSRF_COOKIE_NAME: str = "robin_csrf_token"
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    # --- CORS ---
    # JSON string as list, e.g. '["http://localhost:5173"]'
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 20
    MAX_PDF_PAGES: int = 200
    MAX_DOCUMENTS_PER_COMPANY: int = 100
    MAX_CHUNKS_PER_DOCUMENT: int = 5000
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_BATCH_SIZE: int = 32
    CHUNK_SIZE_TOKENS: int = 200
    CHUNK_OVERLAP_TOKENS: int = 30
    CHROMA_PERSIST_DIR: str = "chroma_data"
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 20
    MAX_CONCURRENT_INGESTIONS: int = 1
    MAX_QUERY_LENGTH: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        # CORS_ORIGINS JSON string se list mein convert karta hai.
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def validate_jwt_secret(self):
        # Production mein weak JWT secret reject karte hain.
        # Authentication enable hone ke baad secret required hai.
        if self.APP_ENV == "production" and len(self.JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters in production."
            )
        if self.MAX_UPLOAD_SIZE_MB <= 0 or self.MAX_PDF_PAGES <= 0:
            raise ValueError("Upload size and PDF page limits must be positive.")
        if self.CHUNK_SIZE_TOKENS <= 0 or self.CHUNK_OVERLAP_TOKENS < 0:
            raise ValueError("Chunk size and overlap must be valid.")
        if self.CHUNK_OVERLAP_TOKENS >= self.CHUNK_SIZE_TOKENS:
            raise ValueError("Chunk overlap must be smaller than chunk size.")
        if self.EMBEDDING_BATCH_SIZE <= 0 or self.MAX_TOP_K <= 0:
            raise ValueError("Embedding batch and top_k limits must be positive.")
        return self

    @property
    def migration_database_url(self) -> str:
        # Migration ke liye direct URL prefer karo, pooled se issues ho sakte hain.
        return self.DATABASE_DIRECT_URL or self.DATABASE_URL

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def upload_directory(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        return path.resolve()

    @property
    def chroma_directory(self) -> Path:
        path = Path(self.CHROMA_PERSIST_DIR)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        return path.resolve()


# Single instance — poori application mein yahi use hoti hai.
settings = Settings()
