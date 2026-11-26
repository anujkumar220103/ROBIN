# Defines validated request and response schemas for the RAG chat endpoint.

import uuid
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# Allowed conversation roles — system prompt injection prevent karne ke liye
# sirf user aur assistant roles accept karte hain.
ALLOWED_ROLES = {"user", "assistant"}


class ConversationMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, max_length=2000)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ALLOWED_ROLES:
            raise ValueError(f"Role must be one of: {ALLOWED_ROLES}")
        return v


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    # History optional hai — frontend React state se bhejta hai.
    history: List[ConversationMessage] = Field(default_factory=list, max_length=6)

    @field_validator("question")
    @classmethod
    def clean_question(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Question cannot be empty or whitespace only.")
        return stripped


class SourceReference(BaseModel):
    source_id: str
    document_id: uuid.UUID
    filename: str
    page_number: int
    chunk_id: str
    excerpt: str
    similarity: float


class ResponseMetadata(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    fallback_used: bool = False
    retrieved_chunks: int = 0
    context_chunks: int = 0
    latency_ms: int = 0


class ChatResponse(BaseModel):
    request_id: str
    status: str  # "answered" | "insufficient_context" | "error"
    answer: str
    sources: List[SourceReference] = Field(default_factory=list)
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class ProviderInfo(BaseModel):
    name: str
    configured: bool
    enabled: bool


class ProvidersStatusResponse(BaseModel):
    providers: List[ProviderInfo]
