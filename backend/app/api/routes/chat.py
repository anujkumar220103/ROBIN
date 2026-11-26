# Authenticated chat endpoint — RAG pipeline ko HTTP API ke through expose karta hai.
# Tenant identity always authenticated user se milti hai, frontend request se nahi.

import logging
import time
import uuid
from collections import defaultdict
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_company, verify_csrf_token
from app.core.config import settings
from app.db.session import get_db
from app.models.company import Company
from app.rag.llm_provider import get_configured_providers
from app.rag.pipeline import run_rag_pipeline
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ProvidersStatusResponse,
    ProviderInfo,
    ResponseMetadata,
    SourceReference,
)

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory rate limiter — single process ke liye sufficient hai.
# Distributed deployment mein Redis-based limiter use karna padega.
# ---------------------------------------------------------------------------

_rate_lock = Lock()
# Maps user_id -> list of request timestamps (epoch seconds).
_user_request_times: dict[str, list[float]] = defaultdict(list)
# Maps user_id -> current concurrent request count.
_user_concurrent: dict[str, int] = defaultdict(int)


def _check_rate_limit(user_id: str) -> None:
    """Enforce per-user rate limit and concurrent request limit."""
    now = time.monotonic()
    window = 60.0  # 1 minute window.

    with _rate_lock:
        # Window se purane timestamps remove karo.
        times = _user_request_times[user_id]
        _user_request_times[user_id] = [t for t in times if now - t < window]

        if len(_user_request_times[user_id]) >= settings.CHAT_RATE_LIMIT_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {settings.CHAT_RATE_LIMIT_PER_MINUTE} requests per minute.",
                headers={"Retry-After": "60"},
            )

        if _user_concurrent[user_id] >= settings.CHAT_MAX_CONCURRENT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many concurrent requests. Please wait for the current request to complete.",
            )

        _user_request_times[user_id].append(now)
        _user_concurrent[user_id] += 1


def _release_concurrent(user_id: str) -> None:
    """Release the concurrent request slot after response is sent."""
    with _rate_lock:
        if _user_concurrent[user_id] > 0:
            _user_concurrent[user_id] -= 1


@router.post("/ask", response_model=ChatResponse)
def ask_question(
    data: ChatRequest,
    _csrf: None = Depends(verify_csrf_token),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Submit a question to the RAG pipeline and receive a grounded answer.

    Authentication required. Company identity derived from authenticated user.
    Frontend cannot override tenant collection or supply provider configuration.

    Privacy notice: Relevant document passages are processed by the configured
    external LLM provider to generate answers. Only minimum necessary context
    is sent — no credentials, tokens, or unrelated documents are transmitted.
    """
    # get_current_company se user ka authenticated company milta hai.
    company_id = current_company.id
    user_id = str(current_company.id)  # Rate limit by company for simplicity.

    _check_rate_limit(user_id)
    request_id = str(uuid.uuid4())

    try:
        result = run_rag_pipeline(
            db=db,
            company_id=company_id,
            question=data.question,
            history=data.history,
            request_id=request_id,
        )
    except Exception as exc:
        logger.error("[%s] Unexpected pipeline error: %s", request_id, exc)
        _release_concurrent(user_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Knowledge assistant is temporarily unavailable.",
        )
    finally:
        _release_concurrent(user_id)

    # Map pipeline result to response schema.
    pipeline_status = result.get("status", "error")
    if pipeline_status == "invalid_input":
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result["answer"])
    if pipeline_status in {"retrieval_error", "provider_error"}:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=result["answer"])

    sources = []
    for src in result.get("sources", []):
        try:
            sources.append(SourceReference(
                source_id=src["source_id"],
                document_id=src["document_id"],
                filename=src["filename"],
                page_number=src["page_number"],
                chunk_id=src["chunk_id"],
                excerpt=src["excerpt"],
                similarity=src["similarity"],
            ))
        except Exception:
            continue

    meta = result.get("metadata", {})
    return ChatResponse(
        request_id=result["request_id"],
        status=pipeline_status,
        answer=result["answer"],
        sources=sources,
        metadata=ResponseMetadata(
            provider=meta.get("provider"),
            model=meta.get("model"),
            fallback_used=meta.get("fallback_used", False),
            retrieved_chunks=meta.get("retrieved_chunks", 0),
            context_chunks=meta.get("context_chunks", 0),
            latency_ms=meta.get("latency_ms", 0),
        ),
    )


@router.get("/providers/status", response_model=ProvidersStatusResponse)
def providers_status(
    current_company: Company = Depends(get_current_company),
):
    """Return safe provider configuration status.

    API keys expose nahi karta — sirf 'configured' aur 'enabled' boolean return karta hai.
    Yahan se provider ko actual call nahi karte (no billable requests).
    """
    providers_data = get_configured_providers()
    return ProvidersStatusResponse(
        providers=[
            ProviderInfo(
                name=p["name"],
                configured=p["configured"],
                enabled=p["enabled"],
            )
            for p in providers_data
        ]
    )
