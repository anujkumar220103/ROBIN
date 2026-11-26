"""One-time migration: copy local tenant collections to Chroma Cloud."""

import sys
from pathlib import Path

import chromadb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.rag.vector_store import get_or_create_collection


def main() -> None:
    if not all((settings.CHROMA_API_KEY, settings.CHROMA_TENANT, settings.CHROMA_DATABASE)):
        raise RuntimeError("Chroma Cloud environment variables are not configured.")

    local_client = chromadb.PersistentClient(path=str(settings.chroma_directory))
    migrated = 0
    for local_collection in local_client.list_collections():
        metadata = local_collection.metadata or {}
        company_id = metadata.get("company_id")
        model_name = metadata.get("embedding_model", settings.EMBEDDING_MODEL)
        dimension = int(metadata.get("embedding_dimension", 384))
        if not company_id:
            continue

        data = local_collection.get(include=["documents", "embeddings", "metadatas"])
        ids = data["ids"]
        if not ids:
            continue
        import uuid
        cloud_collection = get_or_create_collection(
            uuid.UUID(company_id),
            model_name,
            dimension,
        )
        cloud_collection.upsert(
            ids=ids,
            embeddings=data["embeddings"],
            documents=data["documents"],
            metadatas=data["metadatas"],
        )
        migrated += len(ids)
        print(f"MIGRATED {len(ids)} vectors for company {company_id}")
    print(f"TOTAL MIGRATED VECTORS: {migrated}")


if __name__ == "__main__":
    main()
