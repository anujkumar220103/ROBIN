import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from qdrant_client import QdrantClient, models

from app.core.config import Settings
from app.rag import vector_store


def _chunk(company_id, document_id):
    return {
        "chunk_id": f"{document_id}:chunk:000000",
        "text": "The office is closed on Monday.",
        "company_id": str(company_id),
        "document_id": str(document_id),
        "filename": "holidays.pdf",
        "page_number": 1,
        "chunk_index": 0,
        "embedding_model": "test-embedding-model",
    }


def test_production_requires_qdrant_cloud_credentials():
    with pytest.raises(ValidationError, match="QDRANT_URL and QDRANT_API_KEY"):
        Settings(
            APP_ENV="production",
            JWT_SECRET_KEY="a" * 32,
            WIDGET_SESSION_SECRET="b" * 32,
        )


def test_upsert_and_delete_are_scoped_by_tenant_and_document(monkeypatch):
    company_id = uuid.uuid4()
    document_id = uuid.uuid4()
    client = QdrantClient(":memory:")
    monkeypatch.setattr(vector_store.settings, "EMBEDDING_DIMENSION", 2)
    monkeypatch.setattr(
        vector_store,
        "get_vector_store",
        lambda: SimpleNamespace(_client=client),
    )
    try:
        vector_store.upsert_chunks(
            company_id,
            [_chunk(company_id, document_id)],
            [[1.0, 0.0]],
            vector_store.settings.EMBEDDING_MODEL,
            2,
        )

        stored = client.scroll(
            collection_name=vector_store.collection_name(),
            with_payload=True,
            limit=10,
        )[0]
        assert len(stored) == 1
        assert stored[0].payload["company_id"] == str(company_id)
        assert stored[0].payload["document_id"] == str(document_id)
        assert stored[0].payload["chunk_id"] == f"{document_id}:chunk:000000"
        vector_store.delete_document_vectors(company_id, document_id)
        assert client.count(vector_store.collection_name()).count == 0
    finally:
        client.close()


def test_search_filters_by_company_ready_documents_and_embedding(monkeypatch):
    company_id = uuid.uuid4()
    document_id = uuid.uuid4()
    foreign_company = uuid.uuid4()
    query_points = MagicMock(return_value=SimpleNamespace(points=[
        SimpleNamespace(
            payload={
                "chunk_id": f"{document_id}:chunk:000000",
                "text": "The office is closed on Monday.",
                "company_id": str(company_id),
                "document_id": str(document_id),
                "filename": "holidays.pdf",
                "page_number": 1,
                "embedding_model": "test-embedding-model",
            },
            score=0.9,
        ),
        SimpleNamespace(
            payload={
                "chunk_id": "foreign:chunk:000000",
                "text": "Must not be returned.",
                "company_id": str(foreign_company),
                "document_id": str(document_id),
                "filename": "foreign.pdf",
                "page_number": 1,
                "embedding_model": "test-embedding-model",
            },
            score=0.9,
        ),
    ]))
    client = SimpleNamespace(
        collection_exists=MagicMock(return_value=True),
        query_points=query_points,
    )
    monkeypatch.setattr(
        "app.rag.retriever.get_vector_store",
        lambda: SimpleNamespace(_client=client),
    )
    monkeypatch.setattr(
        "app.rag.retriever.get_embedding_model",
        lambda: SimpleNamespace(embed_query=lambda query: [1.0, 0.0]),
    )
    monkeypatch.setattr(
        "app.rag.retriever.settings.EMBEDDING_MODEL",
        "test-embedding-model",
    )

    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [
        SimpleNamespace(id=document_id),
    ]

    from app.rag.retriever import search_company_knowledge

    results = search_company_knowledge(db, company_id, "holiday", top_k=5)

    assert len(results) == 1
    assert results[0]["text"] == "The office is closed on Monday."
    assert results[0]["similarity"] == 0.9
    assert abs(results[0]["distance"] - 0.1) < 1e-9
    query_filter = query_points.call_args.kwargs["query_filter"]
    conditions = {condition.key: condition for condition in query_filter.must}
    assert conditions["company_id"].match.value == str(company_id)
    assert conditions["document_id"].match.any == [str(document_id)]
    assert conditions["embedding_model"].match.value == "test-embedding-model"


def test_model_and_dimension_use_separate_qdrant_collections():
    legacy = vector_store.collection_name("sentence-transformers/all-MiniLM-L6-v2", 384)
    jina = vector_store.collection_name("jina-embeddings-v3", 1024)
    reduced_jina = vector_store.collection_name("jina-embeddings-v3", 512)

    assert len({legacy, jina, reduced_jina}) == 3
