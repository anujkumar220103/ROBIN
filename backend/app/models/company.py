# Defines the Company ORM model — each company is one tenant in the system.

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    # Slug URL-friendly identifier hai — company naam se generate hota hai.
    # Authorization ke liye UUID use hota hai, slug se nahi.
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # One company can have many users (future phase will add more).
    users: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]
        "User", back_populates="company", lazy="select"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="company", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} slug={self.slug!r}>"
