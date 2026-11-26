# Unit tests for password hashing and JWT generation/verification.
# These tests do not require a database connection.

import time
import uuid

import jwt
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# Password hashing tests
# ---------------------------------------------------------------------------

def test_hash_password_produces_hash():
    hashed = hash_password("MySecurePassword123!")
    assert hashed != "MySecurePassword123!"
    assert len(hashed) > 20


def test_verify_correct_password():
    plain = "CorrectHorseBatteryStaple42!"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_wrong_password():
    hashed = hash_password("CorrectPassword123!")
    assert verify_password("WrongPassword123!", hashed) is False


def test_two_hashes_of_same_password_are_different():
    # Argon2 uses a random salt — same password, different hash every time.
    plain = "SamePasswordTest123!"
    h1 = hash_password(plain)
    h2 = hash_password(plain)
    assert h1 != h2


# ---------------------------------------------------------------------------
# JWT tests
# ---------------------------------------------------------------------------

def test_create_and_decode_access_token():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["iss"] == "ROBIN AI"
    assert payload["aud"] == "ROBIN AI"


def test_expired_token_is_rejected(monkeypatch):
    """Simulate an expired token by patching expiration minutes to -1."""
    import app.core.security as sec_module
    from app.core import security as sec

    user_id = uuid.uuid4()

    # Manually create an expired token
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings

    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),  # already expired
        "iss": "ROBIN AI",
        "aud": "ROBIN AI",
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_invalid_signature_is_rejected():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_wrong_issuer_rejected():
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings

    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(hours=1),
        "iss": "WRONG_ISSUER",
        "aud": "ROBIN AI",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    with pytest.raises(jwt.InvalidIssuerError):
        decode_access_token(token)


def test_wrong_audience_rejected():
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings

    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(hours=1),
        "iss": "ROBIN AI",
        "aud": "WRONG_AUDIENCE",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    with pytest.raises(jwt.InvalidAudienceError):
        decode_access_token(token)


def test_missing_sub_claim_rejected():
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings

    now = datetime.now(tz=timezone.utc)
    payload = {
        "iat": now,
        "exp": now + timedelta(hours=1),
        "iss": "ROBIN AI",
        "aud": "ROBIN AI",
        # "sub" deliberately missing
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)
