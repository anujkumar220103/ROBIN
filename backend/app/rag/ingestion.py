# Coordinates document ingestion, indexing, retries, and failure cleanup.

from datetime import datetime, timezone
import logging
import threading
import uuid

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document
from app.rag.embeddings import EmbeddingAPIError, get_embedding_model
from app.rag.pdf_loader import iter_pdf_pages
from app.rag.text_cleaner import clean_text
from app.rag.text_splitter import split_pages
from app.rag.vector_store import delete_document_vectors, upsert_chunks
from app.services.storage_service import materialize_document

logger = logging.getLogger(__name__)
_ingestion_semaphore = threading.BoundedSemaphore(settings.MAX_CONCURRENT_INGESTIONS)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def process_document(document_id: uuid.UUID, allow_reindex: bool = False) -> None:
    with _ingestion_semaphore:
        _process_document(document_id, allow_reindex)


def _process_document(document_id: uuid.UUID, allow_reindex: bool) -> None:
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).with_for_update().first()
        reindex_ready_document = (
            allow_reindex
            and document is not None
            and document.status == "ready"
            and document.embedding_model != settings.EMBEDDING_MODEL
        )
        if document is None or (
            document.status not in ("pending", "failed") and not reindex_ready_document
        ):
            return
        document.status = "processing"
        document.error_message = None
        db.commit()

        pdf_path = materialize_document(document.storage_path)
        try:
            model = get_embedding_model()
            chunk_count = 0
            batch: list[dict] = []
            has_extractable_text = False
            vectors_cleared = False

            with iter_pdf_pages(str(pdf_path), settings.MAX_PDF_PAGES) as (page_count, pages):
                for page in pages:
                    cleaned = clean_text(page["text"])
                    if not cleaned:
                        continue
                    has_extractable_text = True
                    page_chunks = split_pages(
                        [{"page_number": page["page_number"], "text": cleaned}],
                        str(document.id),
                        str(document.company_id),
                        document.original_filename,
                        settings.EMBEDDING_MODEL,
                        settings.CHUNK_SIZE_TOKENS,
                        settings.CHUNK_OVERLAP_TOKENS,
                        settings.MAX_CHUNKS_PER_DOCUMENT - chunk_count,
                        start_index=chunk_count,
                    )
                    for chunk in page_chunks:
                        if not vectors_cleared:
                            delete_document_vectors(document.company_id, document.id)
                            vectors_cleared = True
                        batch.append(chunk)
                        chunk_count += 1
                        if len(batch) == settings.EMBEDDING_BATCH_SIZE:
                            _index_batch(
                                model,
                                document.company_id,
                                batch,
                            )
                            batch.clear()

            if not has_extractable_text:
                raise ValueError("This PDF appears to contain scanned images or no extractable text. OCR support is not available.")
            if chunk_count == 0:
                raise ValueError("No searchable text could be generated from this PDF.")
            if batch:
                _index_batch(model, document.company_id, batch)
        finally:
            if str(pdf_path).startswith(str(settings.upload_directory / ".downloads")):
                pdf_path.unlink(missing_ok=True)

        document.page_count = page_count
        document.chunk_count = chunk_count
        document.embedding_model = settings.EMBEDDING_MODEL
        document.processed_at = _utc_now()
        document.status = "ready"
        document.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document is not None:
                safe_message = (
                    str(exc)
                    if isinstance(exc, (ValueError, EmbeddingAPIError))
                    else "Document processing failed. You can retry the document."
                )
                document.status = "failed"
                document.error_message = safe_message[:1000]
                db.commit()
                try:
                    delete_document_vectors(document.company_id, document.id)
                except Exception:
                    logger.exception("Could not clean partial vectors for document %s", document.id)
        except Exception:
            logger.exception("Could not persist ingestion failure for document %s", document_id)
        logger.exception("Document ingestion failed for %s", document_id)
    finally:
        db.close()


def _index_batch(model, company_id: uuid.UUID, chunks: list[dict]) -> None:
    embeddings = model.embed_documents(
        [chunk["text"] for chunk in chunks],
        settings.EMBEDDING_BATCH_SIZE,
    )
    upsert_chunks(
        company_id,
        chunks,
        embeddings,
        settings.EMBEDDING_MODEL,
        model.dimension,
    )
