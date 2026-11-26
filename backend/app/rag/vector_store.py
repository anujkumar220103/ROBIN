# Manages persistent tenant-specific ChromaDB collections.

import threading
import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings


def collection_name(company_id: uuid.UUID) -> str:
    return f"company_{company_id.hex}"


class VectorStore:
    def __init__(self):
        settings.chroma_directory.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_directory),
            settings=ChromaSettings(anonymized_telemetry=False),
        )


_client_lock = threading.Lock()
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        with _client_lock:
            if _vector_store is None:
                _vector_store = VectorStore()
    return _vector_store


def get_or_create_collection(company_id: uuid.UUID, model_name: str, dimension: int):
    store = get_vector_store()
    name = collection_name(company_id)
    collection = store._client.get_or_create_collection(
        name=name,
        metadata={
            "company_id": str(company_id),
            "embedding_model": model_name,
            "embedding_dimension": dimension,
            "distance_metric": "cosine",
            "hnsw:space": "cosine",
        },
    )
    metadata = collection.metadata or {}
    if metadata.get("embedding_model") != model_name:
        raise ValueError("The tenant collection uses an incompatible embedding model.")
    if int(metadata.get("embedding_dimension", dimension)) != dimension:
        raise ValueError("The tenant collection uses an incompatible embedding dimension.")
    return collection


def upsert_chunks(company_id: uuid.UUID, chunks: list[dict], embeddings: list[list[float]],
                  model_name: str, dimension: int) -> None:
    if len(chunks) != len(embeddings):
        raise RuntimeError("Embedding count does not match chunk count.")
    collection = get_or_create_collection(company_id, model_name, dimension)
    collection.upsert(
        ids=[chunk["chunk_id"] for chunk in chunks],
        embeddings=embeddings,
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[{
            "company_id": chunk["company_id"],
            "document_id": chunk["document_id"],
            "filename": chunk["filename"],
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "embedding_model": chunk["embedding_model"],
        } for chunk in chunks],
    )


def delete_document_vectors(company_id: uuid.UUID, document_id: uuid.UUID) -> None:
    store = get_vector_store()
    name = collection_name(company_id)
    if name not in [item.name for item in store._client.list_collections()]:
        return
    collection = store._client.get_collection(name)
    collection.delete(where={"document_id": str(document_id)})
