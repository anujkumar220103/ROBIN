# Tests PDF extraction, text cleaning, page-aware chunk creation, and storage service.

import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pymupdf
import pytest

from app.rag.pdf_loader import extract_pdf_pages
from app.rag.text_cleaner import clean_text
from app.rag.text_splitter import split_pages
from app.services.storage_service import (
    _CLOUDINARY_RESOURCE_TYPE,
    cloudinary_is_configured,
    is_cloudinary_reference,
    _cloudinary_public_id,
    materialize_document,
)


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
        "jina-embeddings-v3",
        chunk_size=200,
        overlap=30,
    )
    assert len(chunks) == 2
    assert chunks[0]["chunk_id"].endswith(":chunk:000000")
    assert chunks[1]["page_number"] == 2


# ---------------------------------------------------------------------------
# storage_service — Cloudinary resource_type correctness
# ---------------------------------------------------------------------------

class TestCloudinaryResourceType:
    def test_resource_type_is_raw_not_image(self):
        """
        PDFs must be uploaded with resource_type='raw'. Using 'image' causes
        Cloudinary to reject or mishandle the upload, resulting in 500 errors.
        """
        assert _CLOUDINARY_RESOURCE_TYPE == "raw", (
            f"Cloudinary resource_type must be 'raw' for PDFs, got {_CLOUDINARY_RESOURCE_TYPE!r}"
        )

    def test_cloudinary_reference_detection(self):
        assert is_cloudinary_reference("cloudinary://folder/doc123") is True
        assert is_cloudinary_reference("/uploads/company-abc/doc123.pdf") is False
        assert is_cloudinary_reference("") is False

    def test_cloudinary_public_id_extraction(self):
        path = "cloudinary://robin-documents/company-abc/doc123"
        assert _cloudinary_public_id(path) == "robin-documents/company-abc/doc123"

    def test_cloudinary_public_id_raises_on_invalid(self):
        with pytest.raises(ValueError, match="Not a Cloudinary"):
            _cloudinary_public_id("/local/path.pdf")
        with pytest.raises(ValueError, match="Invalid Cloudinary"):
            _cloudinary_public_id("cloudinary://")

    def test_upload_uses_raw_resource_type(self):
        """
        Verify that save_upload passes resource_type='raw' to cloudinary.uploader.upload.
        """
        import asyncio
        from app.services.storage_service import save_upload

        async def _fake_read(n):
            # Return content on first call, then empty to signal EOF
            if not hasattr(_fake_read, "_called"):
                _fake_read._called = True
                return b"%PDF-1.4 test content"
            return b""

        mock_upload_file = MagicMock()
        mock_upload_file.read = _fake_read

        fake_result = {"public_id": "robin-documents/company-abc/doc123"}

        with patch("app.services.storage_service.cloudinary_is_configured", return_value=True), \
             patch("app.services.storage_service._configure_cloudinary"), \
             patch("app.services.storage_service.cloudinary.uploader.upload", return_value=fake_result) as mock_cl_upload:

            asyncio.run(save_upload(uuid.uuid4(), uuid.uuid4(), mock_upload_file))

        call_kwargs = mock_cl_upload.call_args[1]
        assert call_kwargs["resource_type"] == "raw", (
            f"Expected resource_type='raw', got {call_kwargs['resource_type']!r}"
        )
        assert call_kwargs["type"] == "authenticated"

    def test_delete_uses_raw_resource_type(self):
        """
        Verify that delete_document_file passes resource_type='raw' to cloudinary.uploader.destroy.
        """
        from app.services.storage_service import delete_document_file

        with patch("app.services.storage_service.cloudinary_is_configured", return_value=True), \
             patch("app.services.storage_service._configure_cloudinary"), \
             patch("app.services.storage_service.cloudinary.uploader.destroy") as mock_destroy:

            delete_document_file("cloudinary://robin-documents/company-abc/doc123")

        call_kwargs = mock_destroy.call_args[1]
        assert call_kwargs["resource_type"] == "raw", (
            f"Expected resource_type='raw', got {call_kwargs['resource_type']!r}"
        )

    def test_materialize_uses_raw_resource_type(self, tmp_path):
        """
        Verify that materialize_document generates signed URL with resource_type='raw'.
        """
        fake_pdf_content = b"%PDF-1.4 fake"
        fake_signed_url = "https://res.cloudinary.com/test/raw/authenticated/s--sig--/doc.pdf"

        with patch("app.services.storage_service.cloudinary_is_configured", return_value=True), \
             patch("app.services.storage_service._configure_cloudinary"), \
             patch("app.services.storage_service.cloudinary.utils.cloudinary_url",
                   return_value=(fake_signed_url, {})) as mock_url, \
             patch("app.services.storage_service.settings") as mock_settings, \
             patch("urllib.request.urlopen") as mock_urlopen:

            mock_settings.upload_directory = tmp_path
            mock_resp = MagicMock()
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.read.side_effect = [fake_pdf_content, b""]
            mock_urlopen.return_value = mock_resp

            materialize_document("cloudinary://robin-documents/company-abc/doc123")

        call_kwargs = mock_url.call_args[1]
        assert call_kwargs["resource_type"] == "raw", (
            f"Expected resource_type='raw', got {call_kwargs['resource_type']!r}"
        )
        assert call_kwargs["type"] == "authenticated"
        assert call_kwargs["sign_url"] is True


# ---------------------------------------------------------------------------
# Upload route — exception logging
# ---------------------------------------------------------------------------

class TestUploadExceptionLogging:
    def test_upload_logs_exception_on_storage_failure(self, caplog):
        """
        When save_upload raises, the upload route must log the exception with
        full traceback (not swallow it silently) before returning 500.
        """
        import asyncio
        import logging
        from fastapi.testclient import TestClient
        from app.main import app
        from app.api.dependencies import get_current_user, get_current_company, verify_csrf_token
        from app.models.user import User
        from app.models.company import Company
        from app.db.session import get_db

        fake_user = MagicMock(spec=User)
        fake_user.id = uuid.uuid4()
        fake_company = MagicMock(spec=Company)
        fake_company.id = uuid.uuid4()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_current_company] = lambda: fake_company
        app.dependency_overrides[verify_csrf_token] = lambda: None
        app.dependency_overrides[get_db] = lambda: mock_db

        try:
            with patch("app.api.routes.documents.save_upload",
                       side_effect=RuntimeError("Cloudinary connection refused")), \
                 caplog.at_level(logging.ERROR, logger="app.api.routes.documents"):
                with TestClient(app) as c:
                    response = c.post(
                        "/api/v1/documents/upload",
                        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
                    )
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_current_company, None)
            app.dependency_overrides.pop(verify_csrf_token, None)
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 500
        assert response.json()["detail"] == "The document could not be stored."
        # The real exception must appear in server logs — not swallowed silently
        assert any("Unhandled exception during upload" in r.message for r in caplog.records), (
            "Upload route must log the exception — found no matching log record"
        )
