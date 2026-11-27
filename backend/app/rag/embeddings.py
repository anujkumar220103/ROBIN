"""Jina AI embeddings used by document indexing and retrieval."""

import json
import logging
import math
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import urllib.error
import urllib.request

from app.core.config import settings

logger = logging.getLogger(__name__)
_EMBEDDINGS_URL = "https://api.jina.ai/v1/embeddings"
_MAX_RETRY_DELAY_SECONDS = 8.0


class EmbeddingAPIError(RuntimeError):
    """A safe, user-presentable embedding service failure."""


class EmbeddingModel:
    def __init__(self, model_name: str, dimension: int):
        self.model_name = model_name
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: list[str], batch_size: int | None = None) -> list[list[float]]:
        if not texts:
            return []
        size = settings.EMBEDDING_BATCH_SIZE if batch_size is None else batch_size
        if size <= 0:
            raise ValueError("Embedding batch size must be positive.")
        vectors = []
        for start in range(0, len(texts), size):
            vectors.extend(self._embed_batch(texts[start:start + size], "retrieval.passage"))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Search query cannot be empty.")
        return self._embed_batch([text], "retrieval.query")[0]

    def _embed_batch(self, texts: list[str], task: str) -> list[list[float]]:
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Embedding inputs must be non-empty text.")
        payload = json.dumps({
            "model": self.model_name,
            "input": texts,
            "task": task,
            "dimensions": self.dimension,
            "normalized": True,
        }).encode("utf-8")
        request = urllib.request.Request(
            _EMBEDDINGS_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {settings.JINA_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        for attempt in range(settings.EMBEDDING_MAX_RETRIES + 1):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=settings.EMBEDDING_TIMEOUT_SECONDS,
                ) as response:
                    if not 200 <= response.status < 300:
                        raise EmbeddingAPIError(
                            f"Jina API request failed (HTTP {response.status})."
                        )
                    response_body = response.read()
            except urllib.error.HTTPError as exc:
                message = self._http_error_message(exc.code)
                if exc.code not in (429, 500, 502, 503, 504):
                    raise EmbeddingAPIError(message) from None
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                if not self._retry(attempt, retry_after, exc.code):
                    raise EmbeddingAPIError(message) from None
                continue
            except (urllib.error.URLError, TimeoutError, OSError):
                if not self._retry(attempt, None, "network"):
                    raise EmbeddingAPIError(
                        "Jina API request failed due to a network error or timeout."
                    ) from None
                continue

            try:
                body = json.loads(response_body)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise EmbeddingAPIError(
                    "Jina API returned an invalid response."
                ) from None
            return self._validate_response(body, len(texts))

        raise EmbeddingAPIError("Jina API request failed after retries.")

    def _retry(self, attempt: int, retry_after: str | None, status: int | str) -> bool:
        if attempt >= settings.EMBEDDING_MAX_RETRIES:
            logger.warning("Jina embedding request exhausted retries (status=%s).", status)
            return False
        backoff = min(
            settings.EMBEDDING_RETRY_BASE_SECONDS * (2 ** attempt),
            _MAX_RETRY_DELAY_SECONDS,
        )
        try:
            requested_delay = float(retry_after) if retry_after is not None else backoff
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                requested_delay = (retry_at - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                requested_delay = backoff
        delay = min(max(requested_delay, 0.0), _MAX_RETRY_DELAY_SECONDS)
        logger.warning(
            "Retrying Jina embedding request (attempt=%d, status=%s).",
            attempt + 1,
            status,
        )
        time.sleep(delay)
        return True

    @staticmethod
    def _http_error_message(status: int) -> str:
        if status in (401, 403):
            return "Jina API authentication failed; check JINA_API_KEY."
        if status == 402:
            return "Jina API quota is exhausted."
        if status == 429:
            return "Jina API rate limit exceeded; retry the operation shortly."
        if 400 <= status < 500:
            return "Jina rejected the embedding request."
        return f"Jina API request failed (HTTP {status})."

    def _validate_response(self, body: object, expected_count: int) -> list[list[float]]:
        if not isinstance(body, dict):
            raise EmbeddingAPIError("Jina API returned an invalid response.")
        data = body.get("data")
        if not isinstance(data, list) or len(data) != expected_count:
            raise EmbeddingAPIError("Jina API returned an unexpected embedding count.")

        ordered: list[list[float] | None] = [None] * expected_count
        for item in data:
            if not isinstance(item, dict):
                raise EmbeddingAPIError("Jina API returned an invalid embedding.")
            index = item.get("index")
            embedding = item.get("embedding")
            if type(index) is not int or not 0 <= index < expected_count:
                raise EmbeddingAPIError("Jina API returned invalid embedding ordering.")
            if ordered[index] is not None:
                raise EmbeddingAPIError("Jina API returned duplicate embedding indexes.")
            if not isinstance(embedding, list) or len(embedding) != self.dimension:
                raise EmbeddingAPIError("Jina API returned an incompatible embedding dimension.")
            vector = []
            for value in embedding:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise EmbeddingAPIError("Jina API returned invalid embedding values.")
                try:
                    number = float(value)
                except OverflowError:
                    raise EmbeddingAPIError(
                        "Jina API returned invalid embedding values."
                    ) from None
                if not math.isfinite(number):
                    raise EmbeddingAPIError("Jina API returned invalid embedding values.")
                vector.append(number)
            ordered[index] = vector

        if any(vector is None for vector in ordered):
            raise EmbeddingAPIError("Jina API returned invalid embedding ordering.")
        return [vector for vector in ordered if vector is not None]


_embedding_model: EmbeddingModel | None = None


def get_embedding_model() -> EmbeddingModel:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel(
            settings.EMBEDDING_MODEL,
            settings.EMBEDDING_DIMENSION,
        )
    return _embedding_model
