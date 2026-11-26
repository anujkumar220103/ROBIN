# Defines document API request and response shapes.

from datetime import datetime
import uuid
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    original_filename: str
    file_size: int
    status: str
    page_count: int
    chunk_count: int
    mime_type: str
    embedding_model: str | None = None
    error_message: str | None = None
    created_at: datetime
    processed_at: datetime | None = None
    is_publicly_searchable: bool = False

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class KnowledgeBaseStats(BaseModel):
    total_documents: int
    ready_documents: int
    processing_documents: int
    pending_documents: int
    failed_documents: int
    total_pages: int
    total_chunks: int
    total_storage_bytes: int


class DocumentVisibilityUpdate(BaseModel):
    is_publicly_searchable: bool
