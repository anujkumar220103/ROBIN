# Defines document metadata and processing lifecycle for tenant knowledge bases.

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    STATUSES = ("pending", "processing", "ready", "failed", "deleting")

    __table_args__ = (
        UniqueConstraint("company_id", "file_hash", name="uq_documents_company_file_hash"),
        CheckConstraint("status IN ('pending','processing','ready','failed','deleting')", name="ck_documents_status"),
        CheckConstraint("file_size >= 0", name="ck_documents_file_size"),
        CheckConstraint("page_count >= 0", name="ck_documents_page_count"),
        CheckConstraint("chunk_count >= 0", name="ck_documents_chunk_count"),
        Index("ix_documents_company_created", "company_id", "created_at"),
        Index("ix_documents_company_status", "company_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_publicly_searchable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    company: Mapped["Company"] = relationship("Company", back_populates="documents")
    uploaded_by_user: Mapped["User"] = relationship("User", back_populates="uploaded_documents")
