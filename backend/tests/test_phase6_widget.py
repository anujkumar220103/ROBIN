# Verifies public widget origin validation and token audience separation.

import jwt

from app.core.config import settings
from app.core.widget_security import create_widget_session, verify_widget_session
from app.services.domain_service import normalize_origin, origin_is_allowed


def test_origin_normalization_rejects_paths_and_credentials():
    assert normalize_origin("https://Example.COM") == "https://example.com"
    assert normalize_origin("https://example.com:443") == "https://example.com"
    try:
        normalize_origin("https://user@example.com")
        assert False
    except ValueError:
        pass


def test_origin_allowlist_uses_exact_match():
    assert origin_is_allowed(["https://example.com"], "https://example.com")
    assert not origin_is_allowed(["https://example.com"], "https://evil-example.com")
    assert not origin_is_allowed(["https://example.com"], "https://example.com.attacker.com")


def test_widget_token_is_bound_to_chatbot_and_origin(monkeypatch):
    monkeypatch.setattr(settings, "WIDGET_SESSION_SECRET", "test-widget-secret-that-is-long-enough")
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-admin-secret")
    token, expires_in = create_widget_session("robin_test", "https://example.com")
    payload = verify_widget_session(token, "robin_test", "https://example.com")
    assert payload["scope"] == "widget:chat"
    assert expires_in > 0
    try:
        verify_widget_session(token, "robin_other", "https://example.com")
        assert False
    except jwt.InvalidTokenError:
        pass
