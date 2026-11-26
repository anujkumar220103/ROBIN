# Provides knowledge base statistics and internal semantic search APIs.

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_company, verify_csrf_token
from app.core.config import settings
from app.db.session import get_db
from app.models.company import Company
from app.models.document import Document
from app.rag.retriever import search_company_knowledge
from app.schemas.document import KnowledgeBaseStats
from app.schemas.search import SearchRequest, SearchResponse, SearchResult

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])


@router.get("/stats", response_model=KnowledgeBaseStats)
def knowledge_base_stats(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    rows = db.query(
        func.count(Document.id),
        func.count(Document.id).filter(Document.status == "ready"),
        func.count(Document.id).filter(Document.status == "processing"),
        func.count(Document.id).filter(Document.status == "pending"),
        func.count(Document.id).filter(Document.status == "failed"),
        func.coalesce(func.sum(Document.page_count), 0),
        func.coalesce(func.sum(Document.chunk_count).filter(Document.status == "ready"), 0),
        func.coalesce(func.sum(Document.file_size), 0),
    ).filter(Document.company_id == current_company.id).one()
    return KnowledgeBaseStats(
        total_documents=rows[0],
        ready_documents=rows[1],
        processing_documents=rows[2],
        pending_documents=rows[3],
        failed_documents=rows[4],
        total_pages=int(rows[5]),
        total_chunks=int(rows[6]),
        total_storage_bytes=int(rows[7]),
    )


@router.post("/search", response_model=SearchResponse)
def knowledge_base_search(
    data: SearchRequest,
    _csrf: None = Depends(verify_csrf_token),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    top_k = min(data.top_k, settings.MAX_TOP_K)
    try:
        results = search_company_knowledge(
            db,
            current_company.id,
            data.query,
            top_k,
            data.document_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except RuntimeError as exc:
        raise HTTPException(503, str(exc))
    return SearchResponse(
        query=data.query,
        results=[SearchResult(**item) for item in results],
        total_results=len(results),
    )
