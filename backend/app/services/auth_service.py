# Handles company registration and user authentication business logic.

import re
import uuid
import logging
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.models.company import Company
from app.models.user import User
from app.schemas.auth import RegisterRequest

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def _generate_slug(name: str) -> str:
    """Convert a company name to a URL-friendly slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:180]


def _unique_slug(db: Session, base_slug: str) -> str:
    """Ensure slug uniqueness by appending a short UUID suffix if needed."""
    slug = base_slug
    if not db.query(Company).filter(Company.slug == slug).first():
        return slug
    # Duplicate slug handle karte hain — concurrent registration safe hoti hai.
    suffix = str(uuid.uuid4())[:8]
    return f"{base_slug[:170]}-{suffix}"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_company_and_admin(
    db: Session, data: RegisterRequest
) -> Tuple[Company, User]:
    """Create a company and its first admin user in a single transaction.

    Company creation aur user creation ek hi transaction mein hote hain —
    agar user creation fail ho to company bhi rollback ho jati hai.
    """
    # Email normalize karo — consistent comparison ke liye lowercase.
    normalized_email = data.email.lower().strip()

    # Check if email already registered — controlled error dete hain.
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise ValueError("email_already_registered")

    base_slug = _generate_slug(data.company_name)
    slug = _unique_slug(db, base_slug)

    company = Company(
        id=uuid.uuid4(),
        name=data.company_name.strip(),
        slug=slug,
        is_active=True,
    )
    db.add(company)
    db.flush()  # company.id generate karo before user FK reference

    # Password ko plain text mein store nahi karte.
    hashed = hash_password(data.password)

    user = User(
        id=uuid.uuid4(),
        company_id=company.id,
        full_name=data.full_name.strip(),
        email=normalized_email,
        password_hash=hashed,
        # Role server side assign hoti hai — frontend se accept nahi karte.
        role=User.ROLE_COMPANY_ADMIN,
        is_active=True,
    )
    db.add(user)

    try:
        db.commit()
        db.refresh(company)
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Registration integrity error: %s", type(exc).__name__)
        # Email ya slug duplicate race condition handle karte hain.
        raise ValueError("registration_conflict") from exc

    return company, user


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def authenticate_user(
    db: Session, email: str, password: str
) -> Tuple[Optional[User], Optional[Company]]:
    """Verify credentials and return (user, company) or (None, None).

    Generic error dete hain — specific email existence nahi batate.
    """
    normalized_email = email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()

    if user is None:
        # Timing attack mitigation — hash karo chahe user mile ya na mile.
        hash_password("dummy_password_for_timing_safety")
        return None, None

    if not verify_password(password, user.password_hash):
        return None, None

    if not user.is_active:
        return None, None

    company = db.query(Company).filter(Company.id == user.company_id).first()
    if company is None or not company.is_active:
        return None, None

    return user, company
