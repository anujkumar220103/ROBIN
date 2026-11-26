# Handles local and Cloudinary PDF storage behind one small storage interface.

import hashlib
import logging
import tempfile
import uuid
import urllib.request
from pathlib import Path

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

# PDFs are binary blobs — Cloudinary resource_type must be "raw", not "image".
# Using "image" causes upload failures or mismatched signed-URL generation.
_CLOUDINARY_RESOURCE_TYPE = "raw"


def cloudinary_is_configured() -> bool:
    return bool(
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    )


def _configure_cloudinary() -> None:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def is_cloudinary_reference(storage_path: str) -> bool:
    return storage_path.startswith("cloudinary://")


def _cloudinary_public_id(storage_path: str) -> str:
    if not is_cloudinary_reference(storage_path):
        raise ValueError("Not a Cloudinary document reference.")
    public_id = storage_path.removeprefix("cloudinary://").strip("/")
    if not public_id:
        raise ValueError("Invalid Cloudinary document reference.")
    return public_id


def validate_storage_path(company_id: uuid.UUID, document_id: uuid.UUID) -> Path:
    root = settings.upload_directory.resolve()
    target = (root / f"company-{company_id}" / f"{document_id}.pdf").resolve()
    if root not in target.parents:
        raise ValueError("Invalid document storage path.")
    return target


async def save_upload(company_id: uuid.UUID, document_id: uuid.UUID, upload: UploadFile) -> tuple[str, str, int]:
    if cloudinary_is_configured():
        _configure_cloudinary()
        digest = hashlib.sha256()
        size = 0
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                temp_path = temp.name
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                        raise ValueError("The PDF exceeds the maximum file size.")
                    digest.update(chunk)
                    temp.write(chunk)

            folder = f"{settings.CLOUDINARY_FOLDER}/{company_id}"
            logger.info(
                "Uploading document %s to Cloudinary folder %s (size=%d bytes)",
                document_id, folder, size,
            )
            result = cloudinary.uploader.upload(
                temp_path,
                folder=folder,
                public_id=str(document_id),
                resource_type=_CLOUDINARY_RESOURCE_TYPE,
                type="authenticated",
                access_mode="authenticated",
                overwrite=False,
                invalidate=True,
            )
            public_id = result["public_id"]
            logger.info("Cloudinary upload succeeded for document %s, public_id=%s", document_id, public_id)
            return f"cloudinary://{public_id}", digest.hexdigest(), size
        except ValueError:
            raise
        except Exception:
            logger.exception("Cloudinary upload failed for document %s", document_id)
            raise
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

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
        return str(target), digest.hexdigest(), size
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def delete_document_file(storage_path: str) -> None:
    if is_cloudinary_reference(storage_path):
        if not cloudinary_is_configured():
            raise ValueError("Cloudinary is not configured.")
        _configure_cloudinary()
        public_id = _cloudinary_public_id(storage_path)
        logger.info("Deleting Cloudinary asset public_id=%s", public_id)
        cloudinary.uploader.destroy(
            public_id,
            resource_type=_CLOUDINARY_RESOURCE_TYPE,
            type="authenticated",
            invalidate=True,
        )
        return

    path = Path(storage_path)
    root = settings.upload_directory.resolve()
    resolved = path.resolve()
    if root not in resolved.parents:
        raise ValueError("Invalid document storage path.")
    resolved.unlink(missing_ok=True)


def materialize_document(storage_path: str) -> Path:
    """Return a local PDF path for extraction or download."""
    if not is_cloudinary_reference(storage_path):
        path = Path(storage_path)
        if not path.is_file():
            raise FileNotFoundError("Stored PDF was not found.")
        return path.resolve()

    if not cloudinary_is_configured():
        raise ValueError("Cloudinary is not configured.")
    _configure_cloudinary()
    public_id = _cloudinary_public_id(storage_path)
    signed_url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type=_CLOUDINARY_RESOURCE_TYPE,
        type="authenticated",
        secure=True,
        sign_url=True,
    )

    temp_dir = settings.upload_directory / ".downloads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{uuid.uuid4().hex}.pdf"
    logger.info("Materialising Cloudinary document to temp file (public_id=%s)", public_id)
    try:
        with urllib.request.urlopen(signed_url, timeout=30) as source:
            with temp_path.open("xb") as target:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)
        return temp_path.resolve()
    except Exception:
        temp_path.unlink(missing_ok=True)
        logger.exception("Failed to download Cloudinary document (public_id=%s)", public_id)
        raise
