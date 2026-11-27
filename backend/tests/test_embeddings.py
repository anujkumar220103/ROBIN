import json
from email.message import Message
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from app.core.config import Settings
from app.rag.embeddings import EmbeddingAPIError, EmbeddingModel


class _Response:
    status = 200

    def __init__(self, data):
        self._data = json.dumps(data).encode()

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _response(vectors):
    return _Response({
        "data": [
            {"index": index, "embedding": vector}
            for index, vector in enumerate(vectors)
        ],
    })


def test_document_embeddings_batch_and_query_task(monkeypatch):
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        payload = json.loads(request.data)
        if payload["task"] == "retrieval.query":
            vectors = [[0.5, 0.5]]
        elif len(payload["input"]) == 2:
            vectors = [[0.1, 0.9], [0.2, 0.8]]
        else:
            vectors = [[0.3, 0.7]]
        return _response(vectors)

    monkeypatch.setattr("app.rag.embeddings.settings.JINA_API_KEY", "test-secret")
    monkeypatch.setattr("app.rag.embeddings.urllib.request.urlopen", fake_urlopen)
    model = EmbeddingModel("jina-embeddings-v3", 2)

    documents = model.embed_documents(["first", "second", "third"], batch_size=2)
    query = model.embed_query("question")

    assert documents == [[0.1, 0.9], [0.2, 0.8], [0.3, 0.7]]
    assert query == [0.5, 0.5]
    assert [json.loads(request.data)["task"] for request, _ in requests] == [
        "retrieval.passage",
        "retrieval.passage",
        "retrieval.query",
    ]
    assert [len(json.loads(request.data)["input"]) for request, _ in requests] == [2, 1, 1]
    assert all(request.get_header("Accept") == "application/json" for request, _ in requests)
    assert all(request.get_header("Authorization") == "Bearer test-secret" for request, _ in requests)
    assert all(timeout > 0 for _, timeout in requests)


def test_response_order_is_restored_using_indexes(monkeypatch):
    monkeypatch.setattr(
        "app.rag.embeddings.urllib.request.urlopen",
        lambda *_args, **_kwargs: _Response({
            "data": [
                {"index": 1, "embedding": [0.2, 0.8]},
                {"index": 0, "embedding": [0.1, 0.9]},
            ],
        }),
    )

    assert EmbeddingModel("jina-embeddings-v3", 2).embed_documents(
        ["first", "second"]
    ) == [[0.1, 0.9], [0.2, 0.8]]


@pytest.mark.parametrize(
    "vectors",
    [
        [[1.0]],
        [[float("nan"), 0.0]],
        [[True, 0.0]],
    ],
)
def test_invalid_embedding_dimensions_and_values_are_rejected(monkeypatch, vectors):
    monkeypatch.setattr(
        "app.rag.embeddings.urllib.request.urlopen",
        lambda *_args, **_kwargs: _response(vectors),
    )

    with pytest.raises(EmbeddingAPIError):
        EmbeddingModel("jina-embeddings-v3", 2).embed_documents(["text"])


def test_rate_limit_retries_with_bounded_retry_after(monkeypatch):
    headers = Message()
    headers["Retry-After"] = "0"
    rate_limit = HTTPError(
        "https://api.jina.ai/v1/embeddings",
        429,
        "Too Many Requests",
        headers,
        BytesIO(b""),
    )
    urlopen = patch(
        "app.rag.embeddings.urllib.request.urlopen",
        side_effect=[rate_limit, _response([[0.5, 0.5]])],
    )
    monkeypatch.setattr("app.rag.embeddings.settings.EMBEDDING_MAX_RETRIES", 1)
    monkeypatch.setattr("app.rag.embeddings.time.sleep", lambda _delay: None)

    with urlopen as mocked:
        result = EmbeddingModel("jina-embeddings-v3", 2).embed_query("question")

    assert result == [0.5, 0.5]
    assert mocked.call_count == 2


def test_network_timeout_retries_with_exponential_backoff(monkeypatch):
    delays = []
    urlopen = patch(
        "app.rag.embeddings.urllib.request.urlopen",
        side_effect=[TimeoutError(), _response([[0.5, 0.5]])],
    )
    monkeypatch.setattr("app.rag.embeddings.settings.EMBEDDING_MAX_RETRIES", 1)
    monkeypatch.setattr("app.rag.embeddings.settings.EMBEDDING_RETRY_BASE_SECONDS", 0.25)
    monkeypatch.setattr("app.rag.embeddings.time.sleep", delays.append)

    with urlopen as mocked:
        result = EmbeddingModel("jina-embeddings-v3", 2).embed_query("question")

    assert result == [0.5, 0.5]
    assert mocked.call_count == 2
    assert delays == [0.25]


def test_quota_exhaustion_fails_without_retry(monkeypatch):
    error = HTTPError(
        "https://api.jina.ai/v1/embeddings",
        402,
        "Payment Required",
        Message(),
        BytesIO(b""),
    )
    urlopen = patch(
        "app.rag.embeddings.urllib.request.urlopen",
        side_effect=error,
    )
    with urlopen as mocked:
        with pytest.raises(EmbeddingAPIError, match="quota is exhausted"):
            EmbeddingModel("jina-embeddings-v3", 2).embed_query("question")

    assert mocked.call_count == 1


def test_authentication_error_does_not_expose_api_key(monkeypatch):
    headers = Message()
    error = HTTPError(
        "https://api.jina.ai/v1/embeddings",
        401,
        "Unauthorized",
        headers,
        BytesIO(b"secret response content"),
    )
    monkeypatch.setattr("app.rag.embeddings.settings.JINA_API_KEY", "do-not-log-this")
    monkeypatch.setattr(
        "app.rag.embeddings.urllib.request.urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
    )

    with pytest.raises(EmbeddingAPIError, match="authentication failed") as raised:
        EmbeddingModel("jina-embeddings-v3", 2).embed_query("question")

    assert "do-not-log-this" not in str(raised.value)
    assert "secret response content" not in str(raised.value)


def test_embedding_configuration_requires_api_key_and_supported_dimensions():
    with pytest.raises(ValueError, match="JINA_API_KEY is required"):
        Settings(JINA_API_KEY="")

    with pytest.raises(ValueError, match="between 1 and 1024"):
        Settings(EMBEDDING_DIMENSION=1025)

    with pytest.raises(ValueError) as raised:
        Settings(
            JINA_API_KEY="do-not-print-this-key",
            EMBEDDING_MODEL="unsupported-model",
        )
    assert "do-not-print-this-key" not in str(raised.value)
