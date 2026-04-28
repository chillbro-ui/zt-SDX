import hashlib
import uuid

from fastapi import APIRouter, Depends, File as UploadFileType, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.file_service import create_file
from app.storage.minio_client import ensure_bucket, upload_file


router = APIRouter(
    prefix="/files",
    tags=["files"],
)


@router.post("/upload")
async def upload(
    owner_id: str,
    file: UploadFile = UploadFileType(...),
    db: Session = Depends(get_db),
):
    content = await file.read()

    filename = file.filename or "unknown"
    content_type = file.content_type or "application/octet-stream"

    sha256 = hashlib.sha256(content).hexdigest()

    stored_name = f"{uuid.uuid4()}-{filename}"

    ensure_bucket()

    upload_file(
        object_name=stored_name,
        content=content,
        content_type=content_type,
    )

    saved = create_file(
        db=db,
        owner_id=owner_id,
        filename=filename,
        stored_name=stored_name,
        mime_type=content_type,
        size=len(content),
        sha256=sha256,
    )

    return {
        "id": str(saved.id),
        "filename": saved.filename,
        "stored_name": saved.stored_name,
        "sha256": saved.sha256,
        "status": saved.status,
    }