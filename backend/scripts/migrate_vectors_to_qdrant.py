"""Idempotently migrate local or Chroma Cloud vectors into Qdrant Cloud."""

import sys
import uuid
from pathlib import Path

import chromadb
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.rag.vector_store import upsert_chunks

_LEGACY_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _source_client():
    source = settings.CHROMA_MIGRATION_SOURCE.strip().lower()
    if source == "cloud":
        credentials = (
            settings.CHROMA_API_KEY,
            settings.CHROMA_TENANT,
            settings.CHROMA_DATABASE,
        )
        if not all(credentials):
            raise RuntimeError(
                "Set CHROMA_API_KEY, CHROMA_TENANT, and CHROMA_DATABASE for cloud migration."
            )
        return chromadb.CloudClient(
            api_key=credentials[0],
            tenant=credentials[1],
            database=credentials[2],
        )
    if source != "local":
        raise ValueError("CHROMA_MIGRATION_SOURCE must be 'local' or 'cloud'.")

    source_path = Path(settings.CHROMA_PERSIST_DIR).resolve()
    if not source_path.is_dir():
        raise FileNotFoundError(f"Local Chroma data directory does not exist: {source_path}")
    return chromadb.PersistentClient(path=str(source_path))


def main() -> None:
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        raise RuntimeError("QDRANT_URL and QDRANT_API_KEY must target Qdrant Cloud.")

    source_client = _source_client()
    migrated = 0
    for collection in source_client.list_collections():
        collection_metadata = collection.metadata or {}
        company_id = collection_metadata.get("company_id")
        if not company_id:
            raise RuntimeError(
                f"Chroma collection {collection.name!r} has no company_id metadata."
            )
        model_name = collection_metadata.get("embedding_model", _LEGACY_EMBEDDING_MODEL)
        total = collection.count()
        for offset in range(0, total, 100):
            data = collection.get(
                limit=100,
                offset=offset,
                include=["documents", "embeddings", "metadatas"],
            )
            chunks = []
            embeddings = data.get("embeddings")
            for index, chunk_id in enumerate(data["ids"]):
                metadata = data["metadatas"][index] or {}
                embedding = embeddings[index] if embeddings is not None else None
                text = data["documents"][index]
                if embedding is None or text is None:
                    raise RuntimeError(
                        f"Chroma collection {collection.name!r} has incomplete vector data."
                    )
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": text,
                    "company_id": str(metadata.get("company_id", company_id)),
                    "document_id": str(metadata["document_id"]),
                    "filename": str(metadata["filename"]),
                    "page_number": int(metadata["page_number"]),
                    "chunk_index": int(metadata["chunk_index"]),
                    "embedding_model": str(metadata.get("embedding_model", model_name)),
                })
            if chunks:
                upsert_chunks(
                    company_id=uuid.UUID(str(company_id)),
                    chunks=chunks,
                    embeddings=[vector.tolist() if hasattr(vector, "tolist") else list(vector)
                                for vector in embeddings],
                    model_name=model_name,
                    dimension=len(embeddings[0]),
                )
                migrated += len(chunks)
        print(f"MIGRATED {total} vectors from {collection.name}")
    print(f"TOTAL MIGRATED VECTORS: {migrated}")


if __name__ == "__main__":
    main()
