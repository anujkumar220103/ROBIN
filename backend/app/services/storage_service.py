# Handles secure, tenant-separated local PDF file storage.

import hashlib
import uuid
from pathlib import Path
from fastapi import UploadFile

from app.core.config import settings


def validate_storage_path(company_id: uuid.UUID, document_id: uuid.UUID) -> Path:
    root = settings.upload_directory.resolve()
    target = (root / f"company-{company_id}" / f"{document_id}.pdf").resolve()
    if root not in target.parents:
        raise ValueError("Invalid document storage path.")
    return target


async def save_upload(company_id: uuid.UUID, document_id: uuid.UUID, upload: UploadFile) -> tuple[Path, str, int]:
    root = settings.upload_directory.resolve()
    company_dir = (root / f"company-{company_id}").resolve()
    if root not in company_dir.parents:
        raise ValueError("Invalid company storage path.")
    company_dir.mkdir(parents=True, exist_ok=True)

    target = validate_storage_path(company_id, document_id)
    digest = hashlib.sha256()
    size = 0
    temp = target.with_suffix(".pdf.part")

    try:
        with temp.open("xb") as output:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    raise ValueError("The PDF exceeds the maximum file size.")
                digest.update(chunk)
                output.write(chunk)
        temp.replace(target)
        return target, digest.hexdigest(), size
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def delete_document_file(storage_path: str) -> None:
    path = Path(storage_path)
    root = settings.upload_directory.resolve()
    resolved = path.resolve()
    if root not in resolved.parents:
        raise ValueError("Invalid document storage path.")
    resolved.unlink(missing_ok=True)
