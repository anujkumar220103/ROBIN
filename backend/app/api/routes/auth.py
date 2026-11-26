# Authentication routes — register, login, logout, and current user endpoints.

import secrets
import uuid
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_company, get_current_user, verify_csrf_token
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    RegisteredCompanyInfo,
    RegisteredUserInfo,
)
from app.schemas.user import UserUpdateRequest
from app.services.auth_service import authenticate_user, register_company_and_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookies(response: Response, user_id: uuid.UUID) -> str:
    """Set the JWT auth cookie and issue a CSRF double-submit cookie.

    HTTP-only cookie ko JavaScript directly read nahi kar sakti.
    CSRF cookie JavaScript readable hoti hai — frontend isko header mein bhejta hai.
    """
    token = create_access_token(user_id)
    csrf_token = secrets.token_urlsafe(32)

    cookie_kwargs = dict(
        httponly=False,  # Will override for auth cookie below
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    # Auth cookie: httponly=True — JavaScript access nahi kar sakta
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    # CSRF cookie: httponly=False — frontend isko header mein copy karta hai
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return csrf_token


def _clear_auth_cookies(response: Response) -> None:
    """Clear auth and CSRF cookies — matching attributes required for deletion."""
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=settings.CSRF_COOKIE_NAME,
        path="/",
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new company and its first admin user.

    Company aur user ek transaction mein create hote hain.
    Role server side assign hota hai — public request se accept nahi karte.
    """
    try:
        company, user = register_company_and_admin(db, data)
    except ValueError as exc:
        error_code = str(exc)
        if error_code == "email_already_registered":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed due to a conflict. Please try again.",
        )

    return RegisterResponse(
        message="Company account created successfully",
        user=RegisteredUserInfo(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
        ),
        company=RegisteredCompanyInfo(
            id=company.id,
            name=company.name,
            slug=company.slug,
        ),
    )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """Authenticate a user and set auth + CSRF cookies."""
    user, company = authenticate_user(db, str(data.email), data.password)

    if user is None or company is None:
        # Generic message — specific details nahi batate ki email exists hai ya nahi.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    csrf_token = _set_auth_cookies(response, user.id)

    return LoginResponse(
        message="Login successful",
        user=RegisteredUserInfo(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
        ),
        company=RegisteredCompanyInfo(
            id=company.id,
            name=company.name,
            slug=company.slug,
        ),
        csrf_token=csrf_token,
    )


# ---------------------------------------------------------------------------
# Me (session restoration)
# ---------------------------------------------------------------------------

@router.get("/me", response_model=MeResponse)
def get_me(
    response: Response,
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
):
    """Return the authenticated user and their company, with a fresh CSRF token.

    Frontend application start par ye endpoint call karta hai
    taaki page refresh ke baad bhi session restore ho sake.
    Cross-origin deployments mein document.cookie se CSRF token read nahi
    hota, isliye token response body mein bhi return karte hain.
    """
    csrf_token = _set_auth_cookies(response, current_user.id)

    return MeResponse(
        user=RegisteredUserInfo(
            id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
            role=current_user.role,
        ),
        company=RegisteredCompanyInfo(
            id=current_company.id,
            name=current_company.name,
            slug=current_company.slug,
        ),
        csrf_token=csrf_token,
    )


# ---------------------------------------------------------------------------
# Update profile (name only)
# ---------------------------------------------------------------------------

@router.patch("/me", response_model=MeResponse)
def update_profile(
    data: UserUpdateRequest,
    request: Request,
    response: Response,
    _csrf: None = Depends(verify_csrf_token),
    current_user: User = Depends(get_current_user),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    """Update the current user's display name."""
    current_user.full_name = data.full_name
    db.commit()
    db.refresh(current_user)

    csrf_token = _set_auth_cookies(response, current_user.id)

    return MeResponse(
        user=RegisteredUserInfo(
            id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
            role=current_user.role,
        ),
        company=RegisteredCompanyInfo(
            id=current_company.id,
            name=current_company.name,
            slug=current_company.slug,
        ),
        csrf_token=csrf_token,
    )


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

@router.post("/logout", response_model=LogoutResponse)
def logout(
    request: Request,
    response: Response,
    _csrf: None = Depends(verify_csrf_token),
):
    """Clear auth and CSRF cookies. Logout is idempotent.

    Note: JWT is stateless — cookie clear karne se existing token copies
    expire nahi hoti. Full revocation future phase mein implement hogi.
    """
    _clear_auth_cookies(response)
    return LogoutResponse(message="Logged out successfully.")
