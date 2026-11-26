import uuid
from types import SimpleNamespace
from unittest.mock import patch

from app.api.dependencies import get_current_company, verify_csrf_token
from app.db.session import get_db
from app.main import app


def test_provider_error_returns_service_unavailable(client):
    company = SimpleNamespace(id=uuid.uuid4())
    app.dependency_overrides[get_current_company] = lambda: company
    app.dependency_overrides[verify_csrf_token] = lambda: None
    app.dependency_overrides[get_db] = lambda: None

    try:
        with patch(
            "app.api.routes.chat.run_rag_pipeline",
            return_value={
                "request_id": str(uuid.uuid4()),
                "status": "provider_error",
                "answer": "The AI service is temporarily unavailable.",
                "sources": [],
                "metadata": {},
            },
        ):
            response = client.post(
                "/api/v1/chat/ask",
                json={"question": "What is the leave policy?"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "The AI service is temporarily unavailable."
