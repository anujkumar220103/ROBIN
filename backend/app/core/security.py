# Handles password hashing and JWT token generation/verification.

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

# pwdlib ka PasswordHash instance with Argon2id algorithm.
# Password ko plain text mein store nahi karte — Argon2 hashing
# database leak hone par bhi passwords ko protect karti hai.
_password_hash = PasswordHash((Argon2Hasher(),))

JWT_ISSUER = "ROBIN AI"
JWT_AUDIENCE = "ROBIN AI"


# ---------------------------------------------------------------------------
# Password utilities
# ---------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using Argon2id."""
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plain password matches the stored hash."""
    return _password_hash.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT utilities
# ---------------------------------------------------------------------------

def create_access_token(user_id: uuid.UUID) -> str:
    """Generate a signed JWT for the given user ID.

    JWT mein user ka UUID store hota hai, company ID nahi.
    Company membership database se load hoti hai — frontend se trust nahi karte.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),   # subject: user UUID
        "iat": now,             # issued at
        "exp": expire,          # expiration
        "iss": JWT_ISSUER,      # issuer
        "aud": JWT_AUDIENCE,    # audience
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT. Raises jwt.PyJWTError on failure.

    JWT verify karne ke baad hi current user ki identity trust karte hain.
    Signature, expiry, issuer, audience — sab verify hote hain.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],  # explicitly restrict algorithms
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={"require": ["sub", "exp", "iat", "iss", "aud"]},
    )


def extract_user_id(token: str) -> Optional[uuid.UUID]:
    """Return the user UUID from a valid token, or None on any failure."""
    try:
        payload = decode_access_token(token)
        return uuid.UUID(payload["sub"])
    except Exception:
        return None
