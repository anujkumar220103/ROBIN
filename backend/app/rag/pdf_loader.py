# Extracts bounded, page-aware text from uploaded PDF documents.

import pymupdf


def extract_pdf_pages(storage_path: str, max_pages: int) -> tuple[list[dict], int]:
    pages: list[dict] = []
    try:
        with pymupdf.open(storage_path) as pdf:
            if pdf.needs_pass:
                raise ValueError("This PDF is encrypted or password-protected.")
            page_count = pdf.page_count
            if page_count == 0:
                raise ValueError("This PDF contains no pages.")
            if page_count > max_pages:
                raise ValueError(f"This PDF exceeds the maximum of {max_pages} pages.")
            for index in range(page_count):
                page = pdf.load_page(index)
                text = page.get_text("text", sort=True)
                pages.append({"page_number": index + 1, "text": text or ""})
        return pages, page_count
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("This PDF could not be opened or parsed.") from exc
