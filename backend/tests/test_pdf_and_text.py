# Tests PDF extraction, text cleaning, and page-aware chunk creation.

import pymupdf

from app.rag.pdf_loader import extract_pdf_pages
from app.rag.text_cleaner import clean_text
from app.rag.text_splitter import split_pages


def test_clean_text_preserves_meaningful_values():
    text = "  Employee leave: 18 days.\r\n\r\nEmail: hr@example.com  "
    cleaned = clean_text(text)
    assert "18 days" in cleaned
    assert "hr@example.com" in cleaned
    assert "\x00" not in cleaned


def test_extract_pdf_preserves_page_numbers(tmp_path):
    path = tmp_path / "sample.pdf"
    pdf = pymupdf.open()
    for text in ("Employee leave policy.", "Office working hours."):
        page = pdf.new_page()
        page.insert_text((72, 72), text)
    pdf.save(path)
    pdf.close()

    pages, count = extract_pdf_pages(str(path), 200)
    assert count == 2
    assert [page["page_number"] for page in pages] == [1, 2]
    assert "Employee leave" in pages[0]["text"]


def test_chunk_ids_are_deterministic_and_page_aware():
    pages = [
        {"page_number": 1, "text": "Employees receive eighteen days of paid annual leave."},
        {"page_number": 2, "text": "Office hours begin at nine in the morning."},
    ]
    chunks = split_pages(
        pages,
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
        "policy.pdf",
        "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size=200,
        overlap=30,
    )
    assert len(chunks) == 2
    assert chunks[0]["chunk_id"].endswith(":chunk:000000")
    assert chunks[1]["page_number"] == 2
