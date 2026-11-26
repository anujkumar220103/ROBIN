# Defines semantic knowledge base search requests and results.

from pydantic import BaseModel, Field
import uuid


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    document_id: uuid.UUID | None = None


class SearchResult(BaseModel):
    document_id: uuid.UUID
    filename: str
    page_number: int
    chunk_id: str
    text: str
    distance: float
    similarity: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int
