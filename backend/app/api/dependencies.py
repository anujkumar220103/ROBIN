# FastAPI dependency functions for authentication and tenant authorization.

import logging
import uuid
from typing import Optional

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CSRF protection
# ---------------------------------------------------------------------------
# CSRF (Cross-Site Request Forgery) — attacker kisi trusted user ka session
# use karke malicious request bhej sakta hai. CORS sirf browser se protect
# karta hai, isliye CSRF token alag se implement karna padta hai.
#
# Strategy: double-submit cookie pattern.
# Browser CSRF cookie automatically bhejta hai, but custom header
# JavaScript se set karna padta hai — cross-site script ye nahi kar sakta.

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def verify_csrf_token(
    request: Request,
    csrf_cookie: Optional[str] = Cookie(default=None, alias=settings.CSRF_COOKIE_NAME),
    x_csrf_token: Optional[str] = Header(default=None, alias="X-CSRF-Token"),
) -> None:
    """Verify double-submit CSRF token for state-changing requests.

    Safe methods (GET, HEAD, OPTIONS) ko skip karte hain — sirf POST, PATCH,
    DELETE jaise state-changing methods ke liye CSRF check hota hai.
    """
    if request.method in SAFE_METHODS:
        return

    # CORS origin check as additional CSRF defense for cross-origin requests.
    origin = request.headers.get("origin")
    if origin and origin not in settings.CORS_ORIGINS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request origin not allowed.",
        )

    if not csrf_cookie or not x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing.",
        )

    if csrf_cookie != x_csrf_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token mismatch.",
        )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def _get_token_from_cookie(request: Request) -> Optional[str]:
    """Extract JWT from the HTTP-only auth cookie."""
    # HTTP-only cookie ko JavaScript directly read nahi kar sakti.
    # Browser authenticated requests ke saath cookie automatically bhejta hai.
    return request.cookies.get(settings.AUTH_COOKIE_NAME)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the authenticated user from the JWT cookie.

    JWT verify karne ke baad hi current user ki identity trust karte hain.
    """
    token = _get_token_from_cookie(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.ExpiredSignatureError,):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable.",
        )

    return user


def get_current_company(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Company:
    """Return the company belonging to the authenticated user.

    Company ID authenticated user se milti hai, frontend request se nahi.
    Isse ek company dusri company ka data access nahi kar sakti.
    """
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if company is None or not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company account is unavailable.",
        )
    return company


def require_company_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the authenticated user has company_admin role."""
    if current_user.role != User.ROLE_COMPANY_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company admin access required.",
        )
    return current_user
