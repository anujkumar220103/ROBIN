"""Extract bounded, page-aware text from uploaded PDF documents."""

from contextlib import contextmanager
from typing import Iterator

import pymupdf


@contextmanager
def iter_pdf_pages(storage_path: str, max_pages: int) -> Iterator[tuple[int, Iterator[dict]]]:
    try:
        pdf = pymupdf.open(storage_path)
    except Exception as exc:
        raise ValueError("This PDF could not be opened or parsed.") from exc

    try:
        if pdf.needs_pass:
            raise ValueError("This PDF is encrypted or password-protected.")
        page_count = pdf.page_count
        if page_count == 0:
            raise ValueError("This PDF contains no pages.")
        if page_count > max_pages:
            raise ValueError(f"This PDF exceeds the maximum of {max_pages} pages.")

        def pages() -> Iterator[dict]:
            try:
                for index in range(page_count):
                    page = pdf.load_page(index)
                    text = page.get_text("text", sort=True)
                    yield {"page_number": index + 1, "text": text or ""}
            except Exception as exc:
                raise ValueError("This PDF could not be opened or parsed.") from exc

        yield page_count, pages()
    finally:
        pdf.close()


def extract_pdf_pages(storage_path: str, max_pages: int) -> tuple[list[dict], int]:
    with iter_pdf_pages(storage_path, max_pages) as (page_count, pages):
        return list(pages), page_count
