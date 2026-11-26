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
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

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
    CHROMA_API_KEY: str = ""
    CHROMA_TENANT: str = ""
    CHROMA_DATABASE: str = ""

    # --- Cloudinary PDF storage ---
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "robin-documents"
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 20
    MAX_CONCURRENT_INGESTIONS: int = 1
    MAX_QUERY_LENGTH: int = 1000

    # --- LLM Providers ---
    # Provider order determines which LLM is tried first, then fallback.
    LLM_PROVIDER_ORDER: str = "gemini,groq,openrouter"
    LLM_ENABLED_PROVIDERS: str = "gemini,groq,openrouter"

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    # OpenRouter (OpenAI-compatible endpoint)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemma-4-31b-it:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Generation settings
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_OUTPUT_TOKENS: int = 1024
    LLM_PROVIDER_TIMEOUT_SECONDS: int = 20
    LLM_MAX_RETRIES: int = 1
    LLM_TOTAL_TIMEOUT_SECONDS: int = 60

    # Retrieval settings
    RAG_RETRIEVAL_TOP_K: int = 10
    RAG_CONTEXT_TOP_K: int = 5
    RAG_MIN_SIMILARITY: float = 0.35
    RAG_MAX_CONTEXT_TOKENS: int = 3000
    RAG_MAX_QUESTION_LENGTH: int = 1000

    # Conversation history
    RAG_MAX_HISTORY_MESSAGES: int = 6
    RAG_MAX_HISTORY_TOKENS: int = 1000

    # Chat rate limiting
    CHAT_RATE_LIMIT_PER_MINUTE: int = 10
    CHAT_MAX_CONCURRENT_REQUESTS: int = 2

    # Public widget sessions
    WIDGET_SESSION_SECRET: str = ""
    WIDGET_SESSION_TTL_MINUTES: int = 30
    WIDGET_SESSION_ISSUER: str = "robin-widget"
    WIDGET_SESSION_AUDIENCE: str = "robin-public-chat"
    PUBLIC_WIDGET_URL: str = "http://localhost:5173/widget"

    # Public API limits
    PUBLIC_SESSION_RATE_LIMIT_PER_MINUTE: int = 10
    PUBLIC_CHAT_RATE_LIMIT_PER_MINUTE: int = 5
    PUBLIC_CHAT_IP_RATE_LIMIT_PER_MINUTE: int = 20
    PUBLIC_CHAT_COMPANY_RATE_LIMIT_PER_MINUTE: int = 30
    PUBLIC_CHAT_COMPANY_DAILY_LIMIT: int = 200
    PUBLIC_CHAT_GLOBAL_DAILY_LIMIT: int = 1000
    PUBLIC_CHAT_MAX_CONCURRENT_PER_COMPANY: int = 2
    PUBLIC_CHAT_MAX_CONCURRENT_GLOBAL: int = 5

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
        if self.APP_ENV == "production" and len(self.WIDGET_SESSION_SECRET) < 32:
            raise ValueError(
                "WIDGET_SESSION_SECRET must be at least 32 characters in production."
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
    def provider_order(self) -> list[str]:
        return [p.strip().lower() for p in self.LLM_PROVIDER_ORDER.split(",") if p.strip()]

    @property
    def enabled_providers(self) -> list[str]:
        return [p.strip().lower() for p in self.LLM_ENABLED_PROVIDERS.split(",") if p.strip()]

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
