import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, cast

from fastapi import APIRouter, Depends, File as UploadFileType, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.services.file_service import (
    create_file,
    create_share,
    delete_file,
    get_file,
    get_share_by_token,
    list_files,
    update_risk,
    update_share_downloads,
)
from app.storage.minio_client import ensure_bucket, get_download_url, upload_file

router = APIRouter(prefix="/files", tags=["files"])


# ─── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload(
    owner_id: str,
    file: UploadFile = UploadFileType(...),
    db: Session = Depends(get_db),
):
    content = await file.read()
    filename = file.filename or "unknown"
    content_type = file.content_type or "application/octet-stream"

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {settings.MAX_UPLOAD_MB}MB.",
        )

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(settings.ALLOWED_FILE_TYPES)}",
        )

    sha256 = hashlib.sha256(content).hexdigest()
    stored_name = f"{uuid.uuid4()}-{filename}"

    ensure_bucket()
    upload_file(object_name=stored_name, content=content, content_type=content_type)

    saved = create_file(
        db=db,
        owner_id=owner_id,
        filename=filename,
        stored_name=stored_name,
        mime_type=content_type,
        size=len(content),
        sha256=sha256,
        status="QUARANTINED",
    )

    return {
        "id": str(saved.id),
        "filename": cast(str, saved.filename),
        "stored_name": cast(str, saved.stored_name),
        "sha256": cast(str, saved.sha256),
        "status": cast(str, saved.status),
    }


# ─── Risk patch (internal — called by worker) ─────────────────────────────────

@router.patch("/{file_id}/risk")
def patch_risk(
    file_id: str,
    risk_score: int,
    status: str,
    db: Session = Depends(get_db),
):
    file = update_risk(db=db, file_id=file_id, risk_score=risk_score, status=status)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {
        "id": str(file.id),
        "risk_score": cast(int, file.risk_score),
        "status": cast(str, file.status),
    }


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get("/")
def get_files(
    owner_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    files = list_files(db, owner_id=owner_id)
    return {
        "files": [
            {
                "id": str(f.id),
                "filename": cast(str, f.filename),
                "size": cast(int, f.size),
                "mime_type": cast(str, f.mime_type),
                "sensitivity": cast(str, f.sensitivity),
                "status": cast(str, f.status),
                "risk_score": cast(int, f.risk_score),
                "sha256": cast(str, f.sha256),
                "created_at": cast(datetime, f.created_at).isoformat() if cast(Optional[datetime], f.created_at) else None,
            }
            for f in files
        ]
    }


# ─── Shares — MUST be before /{file_id} to avoid route conflict ───────────────

@router.post("/shares")
def create_share_endpoint(
    file_id: str,
    recipient_email: str,
    expiry_hours: int = 24,
    max_downloads: int = 1,
    device_lock: bool = False,
    watermark: bool = True,
    db: Session = Depends(get_db),
):
    file = get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    if cast(str, file.status) == "QUARANTINED":
        raise HTTPException(
            status_code=403,
            detail="Cannot share a quarantined file. Wait for DLP scan to complete.",
        )

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expiry = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

    share = create_share(
        db=db,
        file_id=file_id,
        token_hash=token_hash,
        recipient=recipient_email,
        expiry=expiry,
        downloads_left=max_downloads,
        device_lock=device_lock,
        watermark=watermark,
    )

    return {
        "share_id": str(share.id),
        "share_token": token,
        "recipient": recipient_email,
        "expiry": expiry.isoformat(),
        "max_downloads": max_downloads,
        "device_lock": device_lock,
        "watermark": watermark,
    }


@router.get("/shares/{share_token}")
def download_via_share(
    share_token: str,
    db: Session = Depends(get_db),
):
    token_hash = hashlib.sha256(share_token.encode()).hexdigest()
    share = get_share_by_token(db, token_hash)

    if share is None:
        raise HTTPException(status_code=404, detail="Share not found")

    if cast(str, share.status) != "ACTIVE":
        raise HTTPException(status_code=403, detail=f"Share is {share.status}")

    share_expiry = cast(Optional[datetime], share.expiry)
    if share_expiry and share_expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        setattr(share, "status", "EXPIRED")
        db.commit()
        raise HTTPException(status_code=403, detail="Share link has expired")

    if cast(int, share.downloads_left) <= 0:
        raise HTTPException(status_code=403, detail="Share download limit exhausted")

    file = get_file(db, str(share.file_id))
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    if cast(str, file.status) == "QUARANTINED":
        raise HTTPException(status_code=403, detail="File is quarantined")

    update_share_downloads(db, str(share.id))
    presigned_url = get_download_url(cast(str, file.stored_name))

    share_watermark: Optional[str] = (
        f"{share.recipient}|{str(share.id)}|{datetime.now(timezone.utc).isoformat()}"
        if bool(share.watermark)
        else None
    )

    return {
        "id": str(file.id),
        "filename": cast(str, file.filename),
        "download_url": presigned_url,
        "sha256": cast(str, file.sha256),
        "watermark": share_watermark,
        "expires_in_seconds": 60,
    }


# ─── Internal content URL (for worker DLP scan) ───────────────────────────────

@router.get("/content/{stored_name}")
def get_file_content_url(stored_name: str):
    """Internal endpoint — worker fetches presigned URL by stored_name for DLP scanning."""
    presigned_url = get_download_url(stored_name)
    return {"download_url": presigned_url}


# ─── Single file ops — MUST be after /shares and /content ─────────────────────

@router.get("/{file_id}")
def get_file_endpoint(file_id: str, db: Session = Depends(get_db)):
    file = get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {
        "id": str(file.id),
        "filename": cast(str, file.filename),
        "stored_name": cast(str, file.stored_name),
        "size": cast(int, file.size),
        "mime_type": cast(str, file.mime_type),
        "sha256": cast(str, file.sha256),
        "sensitivity": cast(str, file.sensitivity),
        "status": cast(str, file.status),
        "risk_score": cast(int, file.risk_score),
        "created_at": cast(datetime, file.created_at).isoformat() if cast(Optional[datetime], file.created_at) else None,
    }


@router.get("/{file_id}/download")
def download_file(
    file_id: str,
    user_id: str,
    db: Session = Depends(get_db),
):
    file = get_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    if str(file.owner_id) != user_id:
        raise HTTPException(status_code=403, detail="Access denied. You do not own this file.")

    if cast(str, file.status) == "QUARANTINED":
        raise HTTPException(
            status_code=403,
            detail="File is quarantined pending DLP scan. Try again shortly.",
        )

    presigned_url = get_download_url(cast(str, file.stored_name))
    watermark = f"{user_id}|{file_id}|{datetime.now(timezone.utc).isoformat()}"

    return {
        "id": str(file.id),
        "filename": cast(str, file.filename),
        "download_url": presigned_url,
        "sha256": cast(str, file.sha256),
        "watermark": watermark,
        "expires_in_seconds": 60,
    }


@router.delete("/{file_id}")
def delete_file_endpoint(file_id: str, db: Session = Depends(get_db)):
    file = delete_file(db, file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return {"id": str(file.id), "message": "File deleted"}
