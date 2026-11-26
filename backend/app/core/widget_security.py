# Handles signed short-lived widget sessions and origin-bound public access.

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def create_widget_session(public_id: str, origin: str) -> tuple[str, int]:
    secret = settings.WIDGET_SESSION_SECRET or settings.JWT_SECRET_KEY
    if not secret:
        raise RuntimeError("Widget session secret is not configured.")
    ttl = settings.WIDGET_SESSION_TTL_MINUTES
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "bot": public_id,
        "origin": origin,
        "scope": "widget:chat",
        "iss": settings.WIDGET_SESSION_ISSUER,
        "aud": settings.WIDGET_SESSION_AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=ttl),
        "jti": secrets.token_urlsafe(12),
    }
    token = jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)
    return token, ttl * 60


def verify_widget_session(token: str, public_id: str, origin: str) -> dict:
    secret = settings.WIDGET_SESSION_SECRET or settings.JWT_SECRET_KEY
    if not secret:
        raise jwt.InvalidTokenError("Widget session secret is not configured.")
    payload = jwt.decode(
        token,
        secret,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.WIDGET_SESSION_ISSUER,
        audience=settings.WIDGET_SESSION_AUDIENCE,
        options={"require": ["sub", "bot", "origin", "scope", "iat", "exp", "iss", "aud"]},
    )
    if payload["scope"] != "widget:chat" or payload["bot"] != public_id:
        raise jwt.InvalidTokenError("Widget session is not bound to this chatbot.")
    if payload["origin"] != origin:
        raise jwt.InvalidTokenError("Widget session origin does not match.")
    return payload
