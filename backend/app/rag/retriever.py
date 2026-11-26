# Retrieves tenant-owned, ready-document chunks from Qdrant.

import math
import uuid

from qdrant_client import models

from app.core.config import settings
from app.models.document import Document
from app.rag.embeddings import get_embedding_model
from app.rag.vector_store import collection_name, get_vector_store


def search_company_knowledge(db, company_id: uuid.UUID, query: str, top_k: int = 5,
                             public_only: bool = False,
                             document_id: uuid.UUID | None = None) -> list[dict]:
    query = query.strip()
    if not query:
        raise ValueError("Search query cannot be empty.")
    if len(query) > settings.MAX_QUERY_LENGTH:
        raise ValueError("Search query is too long.")

    ready_query = db.query(Document.id).filter(
        Document.company_id == company_id,
        Document.status == "ready",
    )
    if public_only:
        ready_query = ready_query.filter(Document.is_publicly_searchable.is_(True))
    ready_ids = {
        str(row.id)
        for row in ready_query.all()
    }
    if document_id is not None:
        if str(document_id) not in ready_ids:
            return []
        ready_ids &= {str(document_id)}
    if not ready_ids:
        return []

    store = get_vector_store()
    name = collection_name()
    if not store._client.collection_exists(name):
        return []
    try:
        query_embedding = get_embedding_model().embed_query(query)
        response = store._client.query_points(
            collection_name=name,
            query=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="company_id",
                        match=models.MatchValue(value=str(company_id)),
                    ),
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchAny(any=sorted(ready_ids)),
                    ),
                    models.FieldCondition(
                        key="embedding_model",
                        match=models.MatchValue(value=settings.EMBEDDING_MODEL),
                    ),
                ],
            ),
            limit=max(1, top_k),
            with_payload=True,
            with_vectors=False,
        )
    except Exception as exc:
        raise RuntimeError("Knowledge base search is temporarily unavailable.") from exc

    results = []
    for point in response.points:
        metadata = point.payload or {}
        if not metadata or metadata.get("company_id") != str(company_id):
            continue
        if metadata.get("document_id") not in ready_ids:
            continue
        if metadata.get("embedding_model") != settings.EMBEDDING_MODEL:
            continue
        similarity = float(point.score)
        distance_value = 1.0 - similarity
        if not math.isfinite(distance_value) or not math.isfinite(similarity):
            continue
        results.append({
            "document_id": uuid.UUID(metadata["document_id"]),
            "filename": metadata["filename"],
            "page_number": int(metadata["page_number"]),
            "chunk_id": metadata["chunk_id"],
            "text": metadata["text"],
            "distance": distance_value,
            "similarity": similarity,
        })
    return results
