# Coordinates document retrieval and grounded answer generation.
# RAG mein pehle relevant document chunks retrieve hote hain,
# phir LLM un chunks ke basis par answer generate karta hai.

import logging
import time
import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag.context_builder import (
    build_context,
    filter_by_relevance,
    remove_redundant_chunks,
)
from app.rag.llm_provider import invoke_with_fallback
from app.rag.prompts import build_messages
from app.rag.query_processor import build_retrieval_query, validate_question
from app.rag.response_validator import (
    build_sources_list,
    parse_llm_response,
    validate_response,
)
from app.rag.retriever import search_company_knowledge
from app.schemas.chat import ConversationMessage

logger = logging.getLogger(__name__)


def run_rag_pipeline(
    db: Session,
    company_id: uuid.UUID,
    question: str,
    history: Optional[list[ConversationMessage]] = None,
    request_id: Optional[str] = None,
    public_only: bool = False,
) -> dict:
    """Main RAG pipeline — retrieval se answer generation tak ka pura flow.

    Returns a dict with: status, answer, sources, metadata.
    Caller should never supply arbitrary collection names or company IDs —
    company_id must come from the authenticated user dependency.
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    history = history or []
    pipeline_start = time.monotonic()

    # 1. Question validate karo.
    try:
        question = validate_question(question)
    except ValueError as exc:
        return _error_response(request_id, str(exc), "invalid_input")

    # 2. Retrieval query prepare karo — follow-up questions ke liye context add karo.
    retrieval_query = build_retrieval_query(question, history)

    # 3. Company-specific ChromaDB collection se chunks retrieve karo.
    retrieval_start = time.monotonic()
    try:
        raw_chunks = search_company_knowledge(
            db,
            company_id,
            retrieval_query,
            top_k=settings.RAG_RETRIEVAL_TOP_K,
            public_only=public_only,
        )
    except ValueError as exc:
        return _error_response(request_id, str(exc), "invalid_input")
    except RuntimeError as exc:
        return _error_response(request_id, str(exc), "retrieval_error")

    retrieval_ms = int((time.monotonic() - retrieval_start) * 1000)
    logger.info(
        "[%s] Retrieved %d chunks in %dms for company %s",
        request_id, len(raw_chunks), retrieval_ms, company_id,
    )

    # 4. Relevance threshold apply karo — irrelevant chunks filter karo.
    relevant_chunks = filter_by_relevance(raw_chunks, settings.RAG_MIN_SIMILARITY)

    # 5. Redundant chunks remove karo.
    unique_chunks = remove_redundant_chunks(relevant_chunks)

    # 6. Agar koi relevant context nahi mila to LLM call mat karo.
    if not unique_chunks:
        logger.info(
            "[%s] Insufficient context — %d raw chunks, 0 passed threshold %.2f.",
            request_id, len(raw_chunks), settings.RAG_MIN_SIMILARITY,
        )
        return {
            "request_id": request_id,
            "status": "insufficient_context",
            "answer": "I couldn't find enough relevant information in your uploaded documents to answer this question.",
            "sources": [],
            "metadata": {
                "provider": None,
                "model": None,
                "fallback_used": False,
                "retrieved_chunks": len(raw_chunks),
                "context_chunks": 0,
                "latency_ms": int((time.monotonic() - pipeline_start) * 1000),
            },
        }

    # 7. Context construct karo — token budget enforce karo.
    context_text, source_map = build_context(
        unique_chunks,
        max_chunks=settings.RAG_CONTEXT_TOP_K,
        max_context_tokens=settings.RAG_MAX_CONTEXT_TOKENS,
    )

    # 8. LLM ke liye message list banao — system instructions aur context alag rakhte hain.
    messages = build_messages(question, context_text, history)

    # 9. Provider manager invoke karo — automatic fallback enabled hai.
    generation_start = time.monotonic()
    try:
        provider_result = invoke_with_fallback(messages)
    except RuntimeError as exc:
        logger.error("[%s] All LLM providers failed: %s", request_id, exc)
        return {
            "request_id": request_id,
            "status": "provider_error",
            "answer": "The AI service is temporarily unavailable. Please try again shortly.",
            "sources": [],
            "metadata": {
                "provider": None,
                "model": None,
                "fallback_used": False,
                "retrieved_chunks": len(raw_chunks),
                "context_chunks": len(source_map),
                "latency_ms": int((time.monotonic() - pipeline_start) * 1000),
            },
        }

    generation_ms = int((time.monotonic() - generation_start) * 1000)

    # 10. LLM response parse karo.
    try:
        parsed = parse_llm_response(provider_result["answer_text"])
    except ValueError as exc:
        logger.warning("[%s] Failed to parse LLM response: %s", request_id, exc)
        # Raw text se answer extract karo — structured output nahi mila.
        return {
            "request_id": request_id,
            "status": "answered",
            "answer": provider_result["answer_text"][:4000],
            "sources": [],
            "metadata": {
                "provider": provider_result["provider"],
                "model": provider_result["model"],
                "fallback_used": provider_result["fallback_used"],
                "retrieved_chunks": len(raw_chunks),
                "context_chunks": len(source_map),
                "latency_ms": int((time.monotonic() - pipeline_start) * 1000),
            },
        }

    # 11. Citations validate karo — fabricated sources reject karte hain.
    try:
        validated = validate_response(parsed, source_map)
    except ValueError as exc:
        logger.warning("[%s] Response validation failed: %s", request_id, exc)
        return _error_response(request_id, "Response validation failed.", "validation_error")

    # 12. Insufficient context check.
    if validated["insufficient_context"]:
        return {
            "request_id": request_id,
            "status": "insufficient_context",
            "answer": validated["answer"],
            "sources": [],
            "metadata": {
                "provider": provider_result["provider"],
                "model": provider_result["model"],
                "fallback_used": provider_result["fallback_used"],
                "retrieved_chunks": len(raw_chunks),
                "context_chunks": len(source_map),
                "latency_ms": int((time.monotonic() - pipeline_start) * 1000),
            },
        }

    # 13. Sources build karo with actual retrieved metadata.
    sources = build_sources_list(validated["source_ids"], source_map)

    total_ms = int((time.monotonic() - pipeline_start) * 1000)
    logger.info(
        "[%s] Pipeline complete: provider=%s, fallback=%s, chunks=%d->%d, total=%dms",
        request_id,
        provider_result["provider"],
        provider_result["fallback_used"],
        len(raw_chunks),
        len(source_map),
        total_ms,
    )

    return {
        "request_id": request_id,
        "status": "answered",
        "answer": validated["answer"],
        "sources": sources,
        "metadata": {
            "provider": provider_result["provider"],
            "model": provider_result["model"],
            "fallback_used": provider_result["fallback_used"],
            "retrieved_chunks": len(raw_chunks),
            "context_chunks": len(source_map),
            "latency_ms": total_ms,
        },
    }


def _error_response(request_id: str, message: str, error_type: str) -> dict:
    return {
        "request_id": request_id,
        "status": error_type,
        "answer": message,
        "sources": [],
        "metadata": {
            "provider": None,
            "model": None,
            "fallback_used": False,
            "retrieved_chunks": 0,
            "context_chunks": 0,
            "latency_ms": 0,
        },
    }
