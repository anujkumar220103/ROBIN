# Builds bounded context from retrieved document passages.
# Context budget limit karta hai ki LLM ko kitna document text bhejna hai.

import logging
import uuid
from typing import Optional

from app.core.config import settings
from app.rag.query_processor import estimate_tokens

logger = logging.getLogger(__name__)


def filter_by_relevance(chunks: list[dict], min_similarity: float) -> list[dict]:
    """Remove chunks below the similarity threshold.

    Similarity threshold irrelevant chunks ko filter karne mein help karta hai.
    ChromaDB cosine distance use karta hai: similarity = 1 - distance.
    """
    return [c for c in chunks if c.get("similarity", 0.0) >= min_similarity]


def remove_redundant_chunks(chunks: list[dict]) -> list[dict]:
    """Remove duplicate and highly overlapping chunks.

    Overlapping chunks mein same text repeat hota hai — deduplication context improve karta hai.
    """
    seen_chunk_ids: set[str] = set()
    seen_texts: list[str] = []
    unique: list[dict] = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "")
        text = chunk.get("text", "").strip()

        # Exact duplicate chunk ID remove karo.
        if chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk_id)

        # Highly similar text remove karo (simple overlap check).
        is_duplicate = False
        for existing_text in seen_texts:
            overlap = _text_overlap_ratio(text, existing_text)
            if overlap > 0.85:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_texts.append(text)
            unique.append(chunk)

    return unique


def _text_overlap_ratio(text_a: str, text_b: str) -> float:
    """Simple character-level overlap ratio between two text strings."""
    if not text_a or not text_b:
        return 0.0
    shorter = text_a if len(text_a) <= len(text_b) else text_b
    longer = text_a if len(text_a) > len(text_b) else text_b
    if shorter in longer:
        return len(shorter) / len(longer)
    return 0.0


def build_context(
    chunks: list[dict],
    max_chunks: int,
    max_context_tokens: int,
) -> tuple[str, dict]:
    """Construct a formatted context string and a trusted source mapping.

    Returns:
        context_text: Formatted document context for the LLM prompt.
        source_map: Maps source IDs like 'S1' to actual document metadata.
                    Backend generates these — LLM cannot fabricate source IDs.
    """
    if not chunks:
        return "", {}

    selected = chunks[:max_chunks]
    source_map: dict[str, dict] = {}
    context_parts: list[str] = []
    total_tokens = 0

    for index, chunk in enumerate(selected):
        source_id = f"S{index + 1}"
        text = chunk.get("text", "").strip()

        if not text:
            continue

        chunk_tokens = estimate_tokens(text) + 20  # 20 tokens overhead per passage.
        if total_tokens + chunk_tokens > max_context_tokens and index > 0:
            # Context budget exhausted — lower-ranked chunks drop kar dete hain.
            logger.debug("Context budget reached at chunk %d. Stopping.", index + 1)
            break

        # Source mapping backend se generate hota hai — LLM invent nahi kar sakta.
        source_map[source_id] = {
            "document_id": chunk["document_id"],
            "filename": chunk["filename"],
            "page_number": chunk["page_number"],
            "chunk_id": chunk["chunk_id"],
            "text": text,
            "similarity": chunk.get("similarity", 0.0),
        }

        context_parts.append(
            f"[{source_id}]\n"
            f"Document: {chunk['filename']}\n"
            f"Page: {chunk['page_number']}\n"
            f"Content:\n{text}"
        )
        total_tokens += chunk_tokens

    context_text = "\n\n".join(context_parts)
    return context_text, source_map
