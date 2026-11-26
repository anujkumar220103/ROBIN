# Coordinates document ingestion, indexing, retries, and failure cleanup.

from datetime import datetime, timezone
import logging
import uuid

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document
from app.rag.embeddings import get_embedding_model
from app.rag.pdf_loader import extract_pdf_pages
from app.rag.text_cleaner import clean_text
from app.rag.text_splitter import split_pages
from app.rag.vector_store import delete_document_vectors, upsert_chunks

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def process_document(document_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).with_for_update().first()
        if document is None or document.status not in ("pending", "failed"):
            return
        document.status = "processing"
        document.error_message = None
        db.commit()

        pages, page_count = extract_pdf_pages(document.storage_path, settings.MAX_PDF_PAGES)
        cleaned_pages = []
        for page in pages:
            cleaned = clean_text(page["text"])
            if cleaned:
                cleaned_pages.append({"page_number": page["page_number"], "text": cleaned})
        if not cleaned_pages:
            raise ValueError("This PDF appears to contain scanned images or no extractable text. OCR support is not available.")

        model = get_embedding_model()
        chunks = split_pages(
            cleaned_pages,
            str(document.id),
            str(document.company_id),
            document.original_filename,
            settings.EMBEDDING_MODEL,
            settings.CHUNK_SIZE_TOKENS,
            settings.CHUNK_OVERLAP_TOKENS,
            model.tokenizer,
            settings.MAX_CHUNKS_PER_DOCUMENT,
        )
        if not chunks:
            raise ValueError("No searchable text could be generated from this PDF.")

        delete_document_vectors(document.company_id, document.id)
        embeddings = model.embed_documents([chunk["text"] for chunk in chunks], settings.EMBEDDING_BATCH_SIZE)
        upsert_chunks(document.company_id, chunks, embeddings, settings.EMBEDDING_MODEL, model.dimension)

        document.page_count = page_count
        document.chunk_count = len(chunks)
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
                safe_message = str(exc) if isinstance(exc, ValueError) else "Document processing failed. You can retry the document."
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
