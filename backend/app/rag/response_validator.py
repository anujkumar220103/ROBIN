# Validates generated citations against retrieved document sources.
# Citation validation ensure karti hai ki answer mein referenced source
# actual retrieved document se belong karta hai.

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Source ID format: S followed by one or more digits (e.g. S1, S12).
SOURCE_ID_PATTERN = re.compile(r"\bS(\d+)\b")

# Maximum answer length — unbounded answers reject karte hain.
MAX_ANSWER_LENGTH = 8000


def parse_llm_response(raw_text: str) -> dict:
    """Parse and validate the structured JSON response from the LLM.

    LLM kabhi kabhi JSON ke bahar extra text deta hai — isliye JSON extract karte hain.
    Unsafe eval use nahi karte.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("LLM returned an empty response.")

    # JSON block extract karo — markdown code fences handle karte hain.
    text = raw_text.strip()

    # ```json ... ``` blocks handle karo.
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        # Find first { and last } to extract JSON object.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("LLM response must be a JSON object.")

    return data


def validate_response(parsed: dict, source_map: dict) -> dict:
    """Validate the parsed LLM response against the trusted source mapping.

    Fabricated citations reject karte hain — sirf retrieved sources allow hain.
    """
    answer = parsed.get("answer", "")
    source_ids = parsed.get("source_ids", [])
    insufficient = parsed.get("insufficient_context", False)

    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("LLM response missing a valid 'answer' field.")

    if len(answer) > MAX_ANSWER_LENGTH:
        raise ValueError("LLM answer exceeds maximum allowed length.")

    if not isinstance(source_ids, list):
        raise ValueError("'source_ids' must be a list.")

    if not isinstance(insufficient, bool):
        insufficient = bool(insufficient)

    # Validate each cited source against the backend-generated source map.
    validated_source_ids = []
    for sid in source_ids:
        if not isinstance(sid, str):
            continue
        sid = sid.strip().upper()
        if not SOURCE_ID_PATTERN.match(sid):
            logger.warning("Rejecting malformed source ID: %r", sid)
            continue
        if sid not in source_map:
            # LLM ne ek source ID hallucinate kiya jo retrieved nahi tha.
            logger.warning("Rejecting fabricated source ID %r — not in retrieved context.", sid)
            continue
        validated_source_ids.append(sid)

    # Inline citations in answer text bhi check karo.
    inline_citations = set(SOURCE_ID_PATTERN.findall(answer))
    for num in inline_citations:
        sid = f"S{num}"
        if sid not in source_map and sid not in validated_source_ids:
            logger.warning("Answer contains unknown inline citation [%s] — will be preserved but not resolved.", sid)

    # Remove duplicate source IDs.
    seen = set()
    deduped = []
    for sid in validated_source_ids:
        if sid not in seen:
            seen.add(sid)
            deduped.append(sid)

    return {
        "answer": answer.strip(),
        "source_ids": deduped,
        "insufficient_context": insufficient,
    }


def build_sources_list(validated_source_ids: list[str], source_map: dict) -> list[dict]:
    """Convert validated source IDs to full source metadata for the API response.

    Sirf validated sources return karte hain — LLM generated metadata nahi use karte.
    """
    sources = []
    for sid in validated_source_ids:
        if sid not in source_map:
            continue
        entry = source_map[sid]
        sources.append({
            "source_id": sid,
            "document_id": entry["document_id"],
            "filename": entry["filename"],
            "page_number": entry["page_number"],
            "chunk_id": entry["chunk_id"],
            "excerpt": entry["text"][:300],  # Truncate excerpt for response size.
            "similarity": round(entry.get("similarity", 0.0), 4),
        })
    return sources
