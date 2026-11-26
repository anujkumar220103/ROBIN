# Defines the User ORM model — each user belongs to exactly one company.

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # Allowed role values — future phases can extend this.
    ROLE_COMPANY_ADMIN = "company_admin"
    ALLOWED_ROLES = ("company_admin",)

    __table_args__ = (
        # Role constraint — sirf defined values allowed hain.
        CheckConstraint(
            "role IN ('company_admin')",
            name="ck_users_role",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # Company ID user record se milti hai — frontend request se nahi.
    # Isse ek company dusri company ka data access nahi kar sakti.
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Email uniqueness database level par enforce hoti hai.
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # Password ko plain text mein store nahi karte.
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ROLE_COMPANY_ADMIN,
    )
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

    company: Mapped["Company"] = relationship("Company", back_populates="users")  # type: ignore[name-defined]
    uploaded_documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="uploaded_by_user", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
