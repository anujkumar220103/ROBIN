# Manages Qdrant vector storage with tenant-scoped payloads.

import threading
import uuid
from qdrant_client import QdrantClient, models

from app.core.config import settings


def collection_name() -> str:
    return settings.QDRANT_COLLECTION_NAME


class VectorStore:
    def __init__(self):
        if settings.QDRANT_URL:
            self._client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
            )
        else:
            settings.qdrant_directory.mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=str(settings.qdrant_directory))

    def check_connection(self) -> None:
        self._client.get_collections()


_client_lock = threading.Lock()
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        with _client_lock:
            if _vector_store is None:
                _vector_store = VectorStore()
    return _vector_store


def _ensure_collection(dimension: int) -> None:
    store = get_vector_store()
    name = collection_name()
    if not store._client.collection_exists(name):
        try:
            store._client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE,
                ),
            )
        except Exception:
            if not store._client.collection_exists(name):
                raise
        if settings.QDRANT_URL:
            for field_name in ("company_id", "document_id", "embedding_model"):
                store._client.create_payload_index(
                    collection_name=name,
                    field_name=field_name,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )

    info = store._client.get_collection(name)
    vector_config = info.config.params.vectors
    if not isinstance(vector_config, models.VectorParams):
        raise ValueError("Qdrant collection must use a single unnamed vector.")
    if vector_config.size != dimension:
        raise ValueError("The Qdrant collection uses an incompatible embedding dimension.")
    if vector_config.distance != models.Distance.COSINE:
        raise ValueError("The Qdrant collection must use cosine distance.")


def upsert_chunks(company_id: uuid.UUID, chunks: list[dict], embeddings: list[list[float]],
                  model_name: str, dimension: int) -> None:
    if len(chunks) != len(embeddings):
        raise RuntimeError("Embedding count does not match chunk count.")
    if not chunks:
        return
    if any(str(chunk["company_id"]) != str(company_id) for chunk in chunks):
        raise ValueError("A vector chunk belongs to a different company.")
    _ensure_collection(dimension)
    store = get_vector_store()
    store._client.upsert(
        collection_name=collection_name(),
        points=[
            models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"robin-ai:{chunk['chunk_id']}")),
                vector=embedding,
                payload={
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "company_id": chunk["company_id"],
                    "document_id": chunk["document_id"],
                    "filename": chunk["filename"],
                    "page_number": chunk["page_number"],
                    "chunk_index": chunk["chunk_index"],
                    "embedding_model": model_name,
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ],
    )


def delete_document_vectors(company_id: uuid.UUID, document_id: uuid.UUID) -> None:
    store = get_vector_store()
    name = collection_name()
    if not store._client.collection_exists(name):
        return
    store._client.delete(
        collection_name=name,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="company_id",
                        match=models.MatchValue(value=str(company_id)),
                    ),
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=str(document_id)),
                    ),
                ],
            ),
        ),
    )
