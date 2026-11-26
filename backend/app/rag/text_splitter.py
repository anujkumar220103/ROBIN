# Creates page-aware token-bounded chunks with deterministic identifiers.

from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_pages(pages: list[dict], document_id: str, company_id: str, filename: str,
                model_name: str, chunk_size: int = 200, overlap: int = 30,
                tokenizer=None, max_chunks: int = 5000) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=lambda text: len(tokenizer.encode(text, add_special_tokens=True)) if tokenizer else len(text.split()),
    )
    chunks: list[dict] = []
    chunk_index = 0
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
            if tokenizer:
                token_count = len(tokenizer.encode(part, add_special_tokens=True))
                if token_count > chunk_size:
                    part_tokens = tokenizer.encode(part, add_special_tokens=False)
                    part = tokenizer.decode(part_tokens[:chunk_size], skip_special_tokens=True).strip()
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
