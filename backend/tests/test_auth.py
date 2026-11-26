# Integration-style tests for auth endpoints using a mocked database.
# These tests use dependency overrides to avoid requiring a real Neon database.

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.models.company import Company
from app.models.user import User
from app.core.security import hash_password, create_access_token


def _make_company(**kwargs):
    c = Company()
    c.id = kwargs.get("id", uuid.uuid4())
    c.name = kwargs.get("name", "Test Corp")
    c.slug = kwargs.get("slug", "test-corp")
    c.is_active = kwargs.get("is_active", True)
    c.created_at = datetime.now(tz=timezone.utc)
    c.updated_at = datetime.now(tz=timezone.utc)
    return c


def _make_user(company_id, **kwargs):
    u = User()
    u.id = kwargs.get("id", uuid.uuid4())
    u.company_id = company_id
    u.full_name = kwargs.get("full_name", "Test User")
    u.email = kwargs.get("email", "test@example.com")
    u.password_hash = hash_password(kwargs.get("password", "TestPassword123!"))
    u.role = kwargs.get("role", "company_admin")
    u.is_active = kwargs.get("is_active", True)
    u.created_at = datetime.now(tz=timezone.utc)
    u.updated_at = datetime.now(tz=timezone.utc)
    return u


# ---------------------------------------------------------------------------
# Registration endpoint tests (mocked DB)
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_validates_missing_fields(self, client):
        response = client.post("/api/v1/auth/register", json={})
        assert response.status_code == 422

    def test_register_rejects_short_password(self, client):
        response = client.post("/api/v1/auth/register", json={
            "company_name": "Test Corp",
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "short",
        })
        assert response.status_code == 422

    def test_register_rejects_invalid_email(self, client):
        response = client.post("/api/v1/auth/register", json={
            "company_name": "Test Corp",
            "full_name": "Test User",
            "email": "not-an-email",
            "password": "ValidPassword123!",
        })
        assert response.status_code == 422

    def test_register_rejects_empty_company_name(self, client):
        response = client.post("/api/v1/auth/register", json={
            "company_name": "",
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "ValidPassword123!",
        })
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login endpoint tests (mocked DB)
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_missing_fields_returns_422(self, client):
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_login_invalid_credentials_returns_401(self, client):
        """With no real DB, login with any credentials returns 401 or 500 (no DB)."""
        response = client.post("/api/v1/auth/login", json={
            "email": "nobody@example.com",
            "password": "ValidPassword123!",
        })
        # Without a DB configured, this returns 500; with a mock-empty DB it returns 401
        assert response.status_code in (401, 500)

    def test_successful_login_includes_csrf_token_in_body(self):
        """
        Verifies that a successful login response includes csrf_token in the
        JSON body — required because cross-origin JS cannot read Set-Cookie
        headers when frontend and backend are on different domains.
        """
        company = _make_company()
        user = _make_user(company.id)

        from app.api.dependencies import get_current_user, get_current_company

        def override_user():
            return user

        def override_company():
            return company

        # Patch authenticate_user at the route import site, not the service module
        with patch("app.api.routes.auth.authenticate_user", return_value=(user, company)):
            app.dependency_overrides[get_current_user] = override_user
            app.dependency_overrides[get_current_company] = override_company
            with TestClient(app) as c:
                response = c.post("/api/v1/auth/login", json={
                    "email": "test@example.com",
                    "password": "TestPassword123!",
                })
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_current_company, None)

        assert response.status_code == 200
        body = response.json()
        # csrf_token must be present in the response body (not just in Set-Cookie)
        assert "csrf_token" in body, "csrf_token must be in the login response body"
        assert isinstance(body["csrf_token"], str)
        assert len(body["csrf_token"]) > 0
        # Both cookies must be set
        assert "robin_access_token" in response.cookies
        assert "robin_csrf_token" in response.cookies
        # Cookie value must match the body value (double-submit pattern)
        assert response.cookies["robin_csrf_token"] == body["csrf_token"]


# ---------------------------------------------------------------------------
# Protected endpoint — unauthenticated access
# ---------------------------------------------------------------------------

class TestProtectedEndpoints:
    def test_me_without_cookie_returns_401(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_company_me_without_cookie_returns_401(self, client):
        response = client.get("/api/v1/company/me")
        assert response.status_code == 401

    def test_company_patch_without_cookie_returns_401(self, client):
        response = client.patch("/api/v1/company/me", json={"name": "New Name"})
        # Will hit auth check before CSRF check
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# CSRF token delivery tests
# ---------------------------------------------------------------------------

class TestCsrfTokenDelivery:
    def test_me_endpoint_includes_csrf_token_in_body(self):
        """
        GET /auth/me must return csrf_token in the JSON body so that the
        frontend can repopulate the in-memory CSRF store after a page refresh.
        """
        company = _make_company()
        user = _make_user(company.id)

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        from app.api.dependencies import get_current_user, get_current_company
        from app.core.security import create_access_token

        token = create_access_token(user.id)

        def override_db():
            yield mock_db

        def override_user():
            return user

        def override_company():
            return company

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = override_user
        app.dependency_overrides[get_current_company] = override_company

        with TestClient(app) as c:
            # Set auth cookie so the request reaches the endpoint
            c.cookies.set("robin_access_token", token)
            response = c.get("/api/v1/auth/me")

        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_current_company, None)

        assert response.status_code == 200
        body = response.json()
        assert "csrf_token" in body, "csrf_token must be in the /auth/me response body"
        assert isinstance(body["csrf_token"], str)
        assert len(body["csrf_token"]) > 0

    def test_post_without_csrf_header_returns_403(self, client):
        """
        Any state-changing request without X-CSRF-Token header must return 403
        once auth passes. Here we test a request that hits CSRF validation.
        """
        response = client.post("/api/v1/auth/logout")
        # No auth cookie → 403 from CSRF (cookie missing) or 401 from auth
        assert response.status_code in (401, 403)

    def test_csrf_cookie_body_values_match_on_login(self):
        """
        The robin_csrf_token cookie value and the csrf_token body field must
        be identical — this is the double-submit cookie contract.
        """
        company = _make_company()
        user = _make_user(company.id)

        with patch("app.api.routes.auth.authenticate_user", return_value=(user, company)):
            with TestClient(app) as c:
                response = c.post("/api/v1/auth/login", json={
                    "email": "test@example.com",
                    "password": "TestPassword123!",
                })

        assert response.status_code == 200
        body = response.json()
        cookie_value = response.cookies.get("robin_csrf_token")
        assert cookie_value is not None, "robin_csrf_token cookie must be set"
        assert body.get("csrf_token") == cookie_value, (
            "csrf_token in body must equal robin_csrf_token cookie value"
        )
