# Tests for LLM response parsing and citation validation.

import uuid
import pytest
from app.rag.response_validator import (
    parse_llm_response,
    validate_response,
    build_sources_list,
)


def _source_map():
    return {
        "S1": {
            "document_id": uuid.uuid4(),
            "filename": "policy.pdf",
            "page_number": 3,
            "chunk_id": "chunk-001",
            "text": "Employees receive 18 days of annual leave.",
            "similarity": 0.82,
        },
        "S2": {
            "document_id": uuid.uuid4(),
            "filename": "handbook.pdf",
            "page_number": 7,
            "chunk_id": "chunk-002",
            "text": "Remote work is allowed 3 days per week.",
            "similarity": 0.75,
        },
    }


def test_valid_json_parsed():
    raw = '{"answer": "Employees get 18 days. [S1]", "source_ids": ["S1"], "insufficient_context": false}'
    parsed = parse_llm_response(raw)
    assert parsed["answer"] == "Employees get 18 days. [S1]"
    assert parsed["source_ids"] == ["S1"]


def test_json_in_markdown_fence_parsed():
    raw = '```json\n{"answer": "Policy applies.", "source_ids": [], "insufficient_context": false}\n```'
    parsed = parse_llm_response(raw)
    assert parsed["answer"] == "Policy applies."


def test_empty_response_raises():
    with pytest.raises(ValueError, match="empty"):
        parse_llm_response("")


def test_invalid_json_raises():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_llm_response("not json at all")


def test_valid_response_accepted():
    parsed = {"answer": "Employees get 18 days. [S1]", "source_ids": ["S1"], "insufficient_context": False}
    validated = validate_response(parsed, _source_map())
    assert validated["source_ids"] == ["S1"]


def test_fabricated_source_id_rejected():
    parsed = {"answer": "Some answer [S99]", "source_ids": ["S99"], "insufficient_context": False}
    validated = validate_response(parsed, _source_map())
    # S99 not in source_map — should be removed.
    assert "S99" not in validated["source_ids"]


def test_known_source_id_accepted():
    parsed = {"answer": "Policy text [S1]", "source_ids": ["S1", "S2"], "insufficient_context": False}
    validated = validate_response(parsed, _source_map())
    assert "S1" in validated["source_ids"]
    assert "S2" in validated["source_ids"]


def test_duplicate_source_ids_deduped():
    parsed = {"answer": "Policy [S1] [S1]", "source_ids": ["S1", "S1"], "insufficient_context": False}
    validated = validate_response(parsed, _source_map())
    assert validated["source_ids"].count("S1") == 1


def test_insufficient_context_response():
    parsed = {
        "answer": "I could not find the information.",
        "source_ids": [],
        "insufficient_context": True,
    }
    validated = validate_response(parsed, _source_map())
    assert validated["insufficient_context"] is True
    assert validated["source_ids"] == []


def test_missing_answer_raises():
    with pytest.raises(ValueError):
        validate_response({"answer": "", "source_ids": [], "insufficient_context": False}, _source_map())


def test_sources_list_built():
    source_map = _source_map()
    sources = build_sources_list(["S1"], source_map)
    assert len(sources) == 1
    assert sources[0]["source_id"] == "S1"
    assert sources[0]["filename"] == "policy.pdf"
    assert sources[0]["page_number"] == 3


def test_unknown_source_id_skipped_in_list():
    sources = build_sources_list(["S99"], _source_map())
    assert len(sources) == 0
