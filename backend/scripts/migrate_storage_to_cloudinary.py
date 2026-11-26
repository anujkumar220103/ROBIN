"""One-time migration: move existing local PDFs to Cloudinary."""

import sys
import uuid
from pathlib import Path

import cloudinary
import cloudinary.uploader

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.document import Document


def main() -> None:
    if not all((
        settings.CLOUDINARY_CLOUD_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    )):
        raise RuntimeError("Cloudinary environment variables are not configured.")

    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )

    db = SessionLocal()
    try:
        documents = db.query(Document).filter(
            ~Document.storage_path.like("cloudinary://%"),
        ).all()
        for document in documents:
            local_path = Path(document.storage_path)
            if not local_path.is_file():
                print(f"SKIP missing file: {document.id}")
                continue
            result = cloudinary.uploader.upload(
                str(local_path),
                folder=f"{settings.CLOUDINARY_FOLDER}/{document.company_id}",
                public_id=str(document.id),
                resource_type="image",
                type="authenticated",
                access_mode="authenticated",
                overwrite=False,
            )
            document.storage_path = f"cloudinary://{result['public_id']}"
            db.commit()
            print(f"MIGRATED {document.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
