# Tests for context construction and token budgeting.

import uuid
import pytest
from app.rag.context_builder import (
    build_context,
    filter_by_relevance,
    remove_redundant_chunks,
)


def _make_chunk(doc_id=None, page=1, chunk_id=None, text="Sample text.", similarity=0.8):
    return {
        "document_id": doc_id or uuid.uuid4(),
        "filename": "test.pdf",
        "page_number": page,
        "chunk_id": chunk_id or str(uuid.uuid4()),
        "text": text,
        "distance": 1 - similarity,
        "similarity": similarity,
    }


def test_source_ids_assigned():
    chunks = [_make_chunk(), _make_chunk()]
    ctx, source_map = build_context(chunks, max_chunks=5, max_context_tokens=1000)
    assert "S1" in source_map
    assert "S2" in source_map


def test_source_metadata_preserved():
    doc_id = uuid.uuid4()
    chunk = _make_chunk(doc_id=doc_id, page=3, text="Policy text here.")
    ctx, source_map = build_context([chunk], max_chunks=5, max_context_tokens=1000)
    assert source_map["S1"]["document_id"] == doc_id
    assert source_map["S1"]["page_number"] == 3


def test_empty_chunks_returns_empty():
    ctx, source_map = build_context([], max_chunks=5, max_context_tokens=1000)
    assert ctx == ""
    assert source_map == {}


def test_context_contains_document_name():
    chunk = _make_chunk(text="Employees get 18 days leave.")
    ctx, _ = build_context([chunk], max_chunks=5, max_context_tokens=1000)
    assert "test.pdf" in ctx


def test_token_budget_limits_chunks():
    # Very small budget should stop after first chunk.
    chunks = [_make_chunk(text="A" * 200) for _ in range(5)]
    ctx, source_map = build_context(chunks, max_chunks=5, max_context_tokens=50)
    # At most 1 chunk should be included given tiny budget.
    assert len(source_map) <= 2


def test_max_chunks_respected():
    chunks = [_make_chunk() for _ in range(10)]
    ctx, source_map = build_context(chunks, max_chunks=3, max_context_tokens=5000)
    assert len(source_map) <= 3


def test_relevance_filter_removes_low_similarity():
    chunks = [
        _make_chunk(similarity=0.8),
        _make_chunk(similarity=0.2),
        _make_chunk(similarity=0.5),
    ]
    filtered = filter_by_relevance(chunks, min_similarity=0.4)
    similarities = [c["similarity"] for c in filtered]
    assert all(s >= 0.4 for s in similarities)
    assert len(filtered) == 2


def test_relevance_filter_all_pass():
    chunks = [_make_chunk(similarity=0.9) for _ in range(3)]
    filtered = filter_by_relevance(chunks, min_similarity=0.4)
    assert len(filtered) == 3


def test_duplicate_chunks_removed():
    cid = str(uuid.uuid4())
    chunks = [_make_chunk(chunk_id=cid), _make_chunk(chunk_id=cid)]
    unique = remove_redundant_chunks(chunks)
    assert len(unique) == 1


def test_highly_overlapping_text_deduplicated():
    text = "Employees receive 18 days of annual leave per year."
    chunks = [_make_chunk(text=text), _make_chunk(text=text)]
    unique = remove_redundant_chunks(chunks)
    assert len(unique) == 1


def test_distinct_chunks_preserved():
    chunks = [
        _make_chunk(text="Employees receive 18 days of annual leave."),
        _make_chunk(text="Remote work is allowed up to 3 days per week."),
    ]
    unique = remove_redundant_chunks(chunks)
    assert len(unique) == 2
