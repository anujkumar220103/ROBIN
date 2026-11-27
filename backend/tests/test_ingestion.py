from contextlib import contextmanager
import asyncio
from types import SimpleNamespace
import threading
import time
from unittest.mock import Mock
import tracemalloc
import uuid

from app.rag import ingestion
from app.rag.embeddings import EmbeddingAPIError
from app.main import lifespan
from app.models.document import Document


class _Query:
    def __init__(self, document):
        self.document = document

    def filter(self, *_args):
        return self

    def with_for_update(self):
        return self

    def first(self):
        return self.document


class _Session:
    def __init__(self, document):
        self.document = document

    def query(self, *_args):
        return _Query(self.document)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def _document(status="pending", model=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        status=status,
        embedding_model=model,
        storage_path="stored.pdf",
        original_filename="policy.pdf",
        error_message=None,
        page_count=0,
        chunk_count=0,
        processed_at=None,
        is_publicly_searchable=True,
    )


def _configure_ingestion(monkeypatch, document, model, split_pages):
    monkeypatch.setattr(ingestion, "SessionLocal", lambda: _Session(document))
    monkeypatch.setattr(ingestion, "materialize_document", lambda _path: "stored.pdf")
    monkeypatch.setattr(ingestion, "get_embedding_model", lambda: model)
    monkeypatch.setattr(ingestion, "split_pages", split_pages)
    monkeypatch.setattr(ingestion, "delete_document_vectors", Mock())
    indexed_batches = []

    def save_batch(company_id, chunks, embeddings, model_name, dimension):
        indexed_batches.append((company_id, list(chunks), embeddings, model_name, dimension))

    monkeypatch.setattr(ingestion, "upsert_chunks", save_batch)

    @contextmanager
    def pages(*_args):
        yield 2, iter([
            {"page_number": 1, "text": "first page"},
            {"page_number": 2, "text": "second page"},
        ])

    monkeypatch.setattr(ingestion, "iter_pdf_pages", pages)
    monkeypatch.setattr(ingestion, "clean_text", lambda text: text)
    return indexed_batches


def test_ingestion_indexes_in_bounded_batches_and_preserves_page_metadata(monkeypatch):
    document = _document()
    model = SimpleNamespace(
        dimension=2,
        embed_documents=lambda texts, _size: [[float(index), 0.0] for index, _ in enumerate(texts)],
    )

    def chunks_for_page(pages, document_id, company_id, filename, model_name,
                        _chunk_size, _overlap, _max_chunks, start_index):
        page = pages[0]["page_number"]
        return [
            {
                "chunk_id": f"{document_id}:chunk:{index:06d}",
                "company_id": company_id,
                "document_id": document_id,
                "filename": filename,
                "page_number": page,
                "chunk_index": index,
                "text": f"page {page} chunk {index}",
                "embedding_model": model_name,
            }
            for index in range(start_index, start_index + 4)
        ]

    indexed_batches = _configure_ingestion(
        monkeypatch, document, model, chunks_for_page
    )
    monkeypatch.setattr(ingestion.settings, "EMBEDDING_BATCH_SIZE", 3)
    monkeypatch.setattr(ingestion.settings, "MAX_CHUNKS_PER_DOCUMENT", 10)

    ingestion.process_document(document.id)

    assert document.status == "ready"
    assert document.page_count == 2
    assert document.chunk_count == 8
    assert document.embedding_model == ingestion.settings.EMBEDDING_MODEL
    assert document.is_publicly_searchable is True
    assert [len(batch[1]) for batch in indexed_batches] == [3, 3, 2]
    assert max(len(batch[1]) for batch in indexed_batches) <= 3
    assert [chunk["chunk_index"] for batch in indexed_batches for chunk in batch[1]] == list(range(8))
    assert [chunk["page_number"] for batch in indexed_batches for chunk in batch[1]] == [
        1, 1, 1, 1, 2, 2, 2, 2
    ]


def test_reindex_accepts_a_ready_document_with_legacy_model(monkeypatch):
    document = _document(
        status="ready",
        model="sentence-transformers/all-MiniLM-L6-v2",
    )
    model = SimpleNamespace(
        dimension=2,
        embed_documents=lambda texts, _size: [[1.0, 0.0] for _ in texts],
    )

    def one_chunk(pages, document_id, company_id, filename, model_name,
                  _chunk_size, _overlap, _max_chunks, start_index):
        return [{
            "chunk_id": f"{document_id}:chunk:{start_index:06d}",
            "company_id": company_id,
            "document_id": document_id,
            "filename": filename,
            "page_number": pages[0]["page_number"],
            "chunk_index": start_index,
            "text": "reindexed",
            "embedding_model": model_name,
        }]

    _configure_ingestion(monkeypatch, document, model, one_chunk)

    ingestion.process_document(document.id, allow_reindex=True)

    assert document.status == "ready"
    assert document.embedding_model == ingestion.settings.EMBEDDING_MODEL
    assert document.is_publicly_searchable is True


def test_jina_failure_marks_document_retryable_without_leaking_details(monkeypatch):
    document = _document()
    model = SimpleNamespace(
        dimension=2,
        embed_documents=Mock(
            side_effect=EmbeddingAPIError("Jina API authentication failed; check JINA_API_KEY.")
        ),
    )

    def one_chunk(pages, document_id, company_id, filename, model_name,
                  _chunk_size, _overlap, _max_chunks, start_index):
        return [{
            "chunk_id": f"{document_id}:chunk:{start_index:06d}",
            "company_id": company_id,
            "document_id": document_id,
            "filename": filename,
            "page_number": pages[0]["page_number"],
            "chunk_index": start_index,
            "text": "private text",
            "embedding_model": model_name,
        }]

    _configure_ingestion(monkeypatch, document, model, one_chunk)

    ingestion.process_document(document.id)

    assert document.status == "failed"
    assert "authentication failed" in document.error_message
    assert "private text" not in document.error_message
    assert model.embed_documents.call_count == 1


def test_large_ingestion_bounds_embedding_batch_memory(monkeypatch):
    document = _document()
    model = SimpleNamespace(
        dimension=2,
        embed_documents=lambda texts, _size: [[1.0, 0.0] for _ in texts],
    )
    max_batch_size = 0

    def chunks_for_page(pages, document_id, company_id, filename, model_name,
                        _chunk_size, _overlap, _max_chunks, start_index):
        page_number = pages[0]["page_number"]
        return [
            {
                "chunk_id": f"{document_id}:chunk:{index:06d}",
                "company_id": company_id,
                "document_id": document_id,
                "filename": filename,
                "page_number": page_number,
                "chunk_index": index,
                "text": "bounded memory test",
                "embedding_model": model_name,
            }
            for index in range(start_index, start_index + 25)
        ]

    _configure_ingestion(monkeypatch, document, model, chunks_for_page)
    monkeypatch.setattr(ingestion.settings, "EMBEDDING_BATCH_SIZE", 16)
    monkeypatch.setattr(ingestion.settings, "MAX_CHUNKS_PER_DOCUMENT", 5000)

    @contextmanager
    def many_pages(*_args):
        yield 200, iter(
            {"page_number": index + 1, "text": "page text"}
            for index in range(200)
        )

    def discard_batch(_company_id, chunks, _embeddings, _model_name, _dimension):
        nonlocal max_batch_size
        max_batch_size = max(max_batch_size, len(chunks))

    monkeypatch.setattr(ingestion, "iter_pdf_pages", many_pages)
    monkeypatch.setattr(ingestion, "upsert_chunks", discard_batch)
    tracemalloc.start()
    try:
        ingestion.process_document(document.id)
        _current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert document.status == "ready"
    assert document.chunk_count == 5000
    assert max_batch_size == 16
    assert peak_bytes < 5_000_000


def test_document_ingestion_respects_configured_concurrency_limit(monkeypatch):
    active = 0
    max_active = 0
    lock = threading.Lock()

    def process(_document_id, _allow_reindex):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.02)
        with lock:
            active -= 1

    monkeypatch.setattr(ingestion, "_process_document", process)
    threads = [
        threading.Thread(target=ingestion.process_document, args=(uuid.uuid4(),))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert max_active == 1


def test_startup_recovers_interrupted_documents_with_bulk_update(monkeypatch):
    class Query:
        def filter(self, *_args):
            return self

        def update(self, values, synchronize_session):
            self.values = values
            self.synchronize_session = synchronize_session
            return 2

    class Session:
        def __init__(self):
            self.query_result = Query()
            self.committed = False
            self.closed = False

        def query(self, *_args):
            return self.query_result

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    db = Session()
    monkeypatch.setattr("app.db.session.SessionLocal", lambda: db)

    async def run_lifespan():
        from fastapi import FastAPI

        async with lifespan(FastAPI()):
            pass

    asyncio.run(run_lifespan())

    assert db.query_result.synchronize_session is False
    assert db.query_result.values[Document.status] == "failed"
    assert "interrupted" in db.query_result.values[Document.error_message]
    assert db.committed is True
    assert db.closed is True
