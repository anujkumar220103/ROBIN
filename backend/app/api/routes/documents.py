# Provides authenticated tenant document upload and management APIs.

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_company, get_current_user, verify_csrf_token
from app.core.config import settings
from app.models.company import Company
from app.models.document import Document
from app.models.user import User
from app.rag.ingestion import process_document
from app.rag.pdf_loader import extract_pdf_pages
from app.rag.vector_store import delete_document_vectors
from app.schemas.document import DocumentListResponse, DocumentResponse, DocumentUploadResponse, KnowledgeBaseStats
from app.services.storage_service import delete_document_file, save_upload
from app.db.session import get_db

router = APIRouter(prefix="/documents", tags=["Documents"])


def _document_response(document: Document) -> DocumentResponse:
    return DocumentResponse.model_validate(document)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _csrf: None = Depends(verify_csrf_token),
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""
    if len(filename) > 255:
        raise HTTPException(400, "Filename is too long.")
    if "\x00" in filename or "/" in filename or "\\" in filename:
        raise HTTPException(400, "Filename contains unsupported characters.")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(400, "The uploaded file is not a PDF.")

    count = db.query(func.count(Document.id)).filter(Document.company_id == current_company.id).scalar() or 0
    if count >= settings.MAX_DOCUMENTS_PER_COMPANY:
        raise HTTPException(400, "The maximum document count for this company was reached.")

    document_id = uuid.uuid4()
    storage_path = None
    try:
        storage_path, file_hash, file_size = await save_upload(current_company.id, document_id, file)
        try:
            _, page_count = extract_pdf_pages(str(storage_path), settings.MAX_PDF_PAGES)
        except ValueError as exc:
            raise HTTPException(400, str(exc))

        existing = db.query(Document).filter(
            Document.company_id == current_company.id,
            Document.file_hash == file_hash,
        ).first()
        if existing is not None:
            delete_document_file(str(storage_path))
            raise HTTPException(409, "This document already exists in your knowledge base.")

        document = Document(
            id=document_id,
            company_id=current_company.id,
            uploaded_by=current_user.id,
            original_filename=filename,
            storage_path=str(storage_path),
            mime_type="application/pdf",
            file_size=file_size,
            file_hash=file_hash,
            status="pending",
            page_count=page_count,
            chunk_count=0,
        )
        db.add(document)
        try:
            db.commit()
        except Exception:
            db.rollback()
            delete_document_file(str(storage_path))
            raise
        db.refresh(document)
        background_tasks.add_task(process_document, document.id)
        return DocumentUploadResponse(message="Document uploaded successfully", document=_document_response(document))
    except HTTPException:
        if storage_path is not None:
            delete_document_file(str(storage_path))
        raise
    except Exception:
        if storage_path is not None:
            delete_document_file(str(storage_path))
        raise HTTPException(500, "The document could not be stored.")


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    query = db.query(Document).filter(Document.company_id == current_company.id)
    if status_filter:
        if status_filter not in Document.STATUSES:
            raise HTTPException(400, "Invalid document status.")
        query = query.filter(Document.status == status_filter)
    if search:
        query = query.filter(Document.original_filename.ilike(f"%{search[:255]}%"))
    total = query.count()
    items = query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return DocumentListResponse(
        items=[_document_response(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def document_details(
    document_id: uuid.UUID,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id, Document.company_id == current_company.id).first()
    if document is None:
        raise HTTPException(404, "Document not found.")
    return _document_response(document)


@router.get("/{document_id}/download")
def download_document(
    document_id: uuid.UUID,
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(Document.id == document_id, Document.company_id == current_company.id).first()
    if document is None:
        raise HTTPException(404, "Document not found.")
    path = Path(document.storage_path)
    root = settings.upload_directory.resolve()
    if root not in path.resolve().parents or not path.is_file():
        raise HTTPException(404, "Stored PDF was not found.")
    safe_name = document.original_filename.replace('"', "_").replace("\r", "_").replace("\n", "_")
    return FileResponse(path, media_type="application/pdf", filename=safe_name)


@router.delete("/{document_id}", status_code=status.HTTP_202_ACCEPTED)
def delete_document(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    _csrf: None = Depends(verify_csrf_token),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_company.id,
    ).first()
    if document is None:
        raise HTTPException(404, "Document not found.")
    if document.status == "processing":
        raise HTTPException(409, "This document is currently being processed.")
    if document.status == "deleting":
        try:
            delete_document_vectors(document.company_id, document.id)
            delete_document_file(document.storage_path)
            db.delete(document)
            db.commit()
            return {"message": "Document deleted successfully"}
        except Exception:
            db.rollback()
            raise HTTPException(503, "Document cleanup could not be completed. Retry deletion.")

    document.status = "deleting"
    document.error_message = None
    db.commit()
    try:
        delete_document_vectors(document.company_id, document.id)
        delete_document_file(document.storage_path)
        db.delete(document)
        db.commit()
        return {"message": "Document deleted successfully"}
    except Exception:
        db.rollback()
        document = db.query(Document).filter(Document.id == document_id).first()
        if document is not None:
            document.status = "deleting"
            document.error_message = "Document cleanup could not be completed."
            db.commit()
        raise HTTPException(503, "Document cleanup could not be completed. Retry deletion.")


@router.post("/{document_id}/retry", response_model=DocumentUploadResponse)
def retry_document(
    document_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    _csrf: None = Depends(verify_csrf_token),
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_company.id,
    ).first()
    if document is None:
        raise HTTPException(404, "Document not found.")
    if document.status != "failed":
        raise HTTPException(409, "Only failed documents can be retried.")
    path = Path(document.storage_path)
    root = settings.upload_directory.resolve()
    if root not in path.resolve().parents or not path.is_file():
        raise HTTPException(409, "The original PDF is missing and cannot be retried.")

    document.status = "pending"
    document.error_message = None
    document.page_count = 0
    document.chunk_count = 0
    db.commit()
    db.refresh(document)
    background_tasks.add_task(process_document, document.id)
    return DocumentUploadResponse(message="Document retry scheduled", document=_document_response(document))
