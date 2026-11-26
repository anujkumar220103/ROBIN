# Defines one configurable public chatbot owned by each company.

import secrets
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Chatbot(Base):
    __tablename__ = "chatbots"

    __table_args__ = (
        UniqueConstraint("company_id", name="uq_chatbots_company"),
        UniqueConstraint("public_id", name="uq_chatbots_public_id"),
        CheckConstraint("position IN ('bottom-right','bottom-left')", name="ck_chatbots_position"),
        CheckConstraint("char_length(primary_color) = 7", name="ck_chatbots_primary_color"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    public_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, default="Support Assistant")
    description: Mapped[str] = mapped_column(String(300), nullable=False, default="Ask questions about our services.")
    welcome_message: Mapped[str] = mapped_column(Text, nullable=False, default="Hello! How can I help you today?")
    placeholder: Mapped[str] = mapped_column(String(150), nullable=False, default="Type your question...")
    primary_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#2563EB")
    position: Mapped[str] = mapped_column(String(20), nullable=False, default="bottom-right")
    launcher_label: Mapped[str] = mapped_column(String(50), nullable=False, default="Chat with us")
    suggested_questions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    allowed_domains: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_sources: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    company: Mapped["Company"] = relationship("Company", back_populates="chatbot")

    @staticmethod
    def generate_public_id() -> str:
        return f"robin_{secrets.token_urlsafe(24)}"
