# Creates page-aware token-bounded chunks with deterministic identifiers.

from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_pages(pages: list[dict], document_id: str, company_id: str, filename: str,
                model_name: str, chunk_size: int = 200, overlap: int = 30,
                max_chunks: int = 5000, start_index: int = 0) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=lambda text: len(text.split()),
    )
    chunks: list[dict] = []
    chunk_index = start_index
    for page in pages:
        text = (page.get("text") or "").strip()
        if not text:
            continue
        for part in splitter.split_text(text):
            part = part.strip()
            if not part:
                continue
            if len(chunks) >= max_chunks:
                raise ValueError("This document exceeds the maximum supported chunk count.")
            chunks.append({
                "chunk_id": f"{document_id}:chunk:{chunk_index:06d}",
                "company_id": company_id,
                "document_id": document_id,
                "filename": filename,
                "page_number": page["page_number"],
                "chunk_index": chunk_index,
                "text": part,
                "embedding_model": model_name,
            })
            chunk_index += 1
    return chunks
