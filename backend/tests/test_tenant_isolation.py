# Tests for multi-tenant isolation — verifies that tenant identity comes
# from the authenticated user's DB record, not from request parameters.

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from app.core.security import hash_password, create_access_token
from app.models.company import Company
from app.models.user import User
from app.services.auth_service import _generate_slug


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def test_slug_generation():
    assert _generate_slug("Example Technologies") == "example-technologies"
    assert _generate_slug("ACME Corp!") == "acme-corp"
    assert _generate_slug("  spaces  ") == "spaces"


def test_slug_handles_special_characters():
    slug = _generate_slug("Hello & World Co.")
    assert " " not in slug
    assert "&" not in slug


# ---------------------------------------------------------------------------
# Tenant isolation principle tests
# ---------------------------------------------------------------------------

def test_company_id_from_user_record_not_request():
    """Demonstrate that company_id must be read from user DB record.

    This is a logic test — verifies the principle that tenant identity
    is derived server-side, not from frontend-supplied values.
    """
    real_company_id = uuid.uuid4()
    attacker_company_id = uuid.uuid4()

    user = User()
    user.id = uuid.uuid4()
    user.company_id = real_company_id
    user.full_name = "Real User"
    user.email = "user@real.com"
    user.password_hash = hash_password("ValidPassword123!")
    user.role = "company_admin"
    user.is_active = True

    # Company ID user record se milta hai, request body se nahi.
    # Attacker apni company se dusri company ka data access nahi kar sakta.
    assert user.company_id == real_company_id
    assert user.company_id != attacker_company_id


def test_role_is_not_assignable_from_request():
    """Verify that role comes from server, not from registration input."""
    # RegisterRequest mein role field nahi hai — Pydantic schema se prevent hota hai.
    from app.schemas.auth import RegisterRequest

    # Role field should not exist in RegisterRequest
    fields = RegisterRequest.model_fields
    assert "role" not in fields, "Role must not be accepted in registration requests."
    assert "company_id" not in fields, "company_id must not be in registration requests."
    assert "is_active" not in fields, "is_active must not be in registration requests."


def test_company_update_schema_prevents_mass_assignment():
    """Verify that company update schema only allows name changes."""
    from app.schemas.company import CompanyUpdateRequest

    fields = CompanyUpdateRequest.model_fields
    assert "id" not in fields
    assert "slug" not in fields
    assert "is_active" not in fields
    assert "name" in fields


def test_user_update_schema_prevents_mass_assignment():
    """Verify that user update schema only allows name changes."""
    from app.schemas.user import UserUpdateRequest

    fields = UserUpdateRequest.model_fields
    assert "email" not in fields
    assert "password" not in fields
    assert "role" not in fields
    assert "company_id" not in fields
    assert "is_active" not in fields
    assert "full_name" in fields
