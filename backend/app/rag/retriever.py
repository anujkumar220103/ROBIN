# Retrieves tenant-owned, ready-document chunks from ChromaDB.

import math
import uuid

from app.core.config import settings
from app.models.document import Document
from app.rag.embeddings import get_embedding_model
from app.rag.vector_store import collection_name, get_vector_store


def search_company_knowledge(db, company_id: uuid.UUID, query: str, top_k: int = 5,
                             document_id: uuid.UUID | None = None) -> list[dict]:
    query = query.strip()
    if not query:
        raise ValueError("Search query cannot be empty.")
    if len(query) > settings.MAX_QUERY_LENGTH:
        raise ValueError("Search query is too long.")

    ready_ids = {
        str(row.id)
        for row in db.query(Document.id).filter(
            Document.company_id == company_id,
            Document.status == "ready",
        ).all()
    }
    if document_id is not None:
        if str(document_id) not in ready_ids:
            return []
        ready_ids &= {str(document_id)}
    if not ready_ids:
        return []

    store = get_vector_store()
    name = collection_name(company_id)
    if name not in [item.name for item in store._client.list_collections()]:
        return []
    try:
        collection = store._client.get_collection(name)
        query_embedding = get_embedding_model().embed_query(query)
        response = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, max(1, collection.count())),
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        raise RuntimeError("Knowledge base search is temporarily unavailable.") from exc

    ids = response.get("ids", [[]])[0]
    documents = response.get("documents", [[]])[0]
    metadatas = response.get("metadatas", [[]])[0]
    distances = response.get("distances", [[]])[0]
    results = []
    for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
        if not metadata or metadata.get("company_id") != str(company_id):
            continue
        if metadata.get("document_id") not in ready_ids:
            continue
        distance_value = float(distance)
        similarity = 1.0 - distance_value
        if not math.isfinite(distance_value) or not math.isfinite(similarity):
            continue
        results.append({
            "document_id": uuid.UUID(metadata["document_id"]),
            "filename": metadata["filename"],
            "page_number": int(metadata["page_number"]),
            "chunk_id": chunk_id,
            "text": text,
            "distance": distance_value,
            "similarity": similarity,
        })
    return results
