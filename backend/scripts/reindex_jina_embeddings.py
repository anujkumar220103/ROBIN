"""Re-embed stored PDFs with the configured Jina model, one document at a time."""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document
from app.rag.ingestion import process_document

_PAGE_SIZE = 50


def _next_document_ids(after_id: uuid.UUID | None = None) -> list[uuid.UUID]:
    db = SessionLocal()
    try:
        query = db.query(Document.id).filter(
            (
                Document.status.in_(("pending", "failed"))
                | (
                    (Document.status == "ready")
                    & (
                        Document.embedding_model.is_(None)
                        | (Document.embedding_model != settings.EMBEDDING_MODEL)
                    )
                )
            ),
        )
        if after_id is not None:
            query = query.filter(Document.id > after_id)
        return [
            row.id
            for row in query.order_by(Document.id).limit(_PAGE_SIZE).all()
        ]
    finally:
        db.close()


def _document_is_reindexed(document_id: uuid.UUID) -> bool:
    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        return bool(
            document
            and document.status == "ready"
            and document.embedding_model == settings.EMBEDDING_MODEL
        )
    finally:
        db.close()


def main() -> int:
    after_id = None
    succeeded = 0
    failed = 0
    while True:
        document_ids = _next_document_ids(after_id)
        if not document_ids:
            break
        after_id = document_ids[-1]
        for document_id in document_ids:
            process_document(document_id, allow_reindex=True)
            if _document_is_reindexed(document_id):
                succeeded += 1
                print(f"REINDEXED {document_id}")
            else:
                failed += 1
                print(f"FAILED {document_id}")

    print(f"Re-indexing complete: {succeeded} succeeded, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
