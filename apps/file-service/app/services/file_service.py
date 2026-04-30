from datetime import datetime
from typing import Optional, cast

from sqlalchemy.orm import Session

from app.models.file import File
from app.models.share import Share


def create_file(
    db: Session,
    owner_id: str,
    filename: str,
    stored_name: str,
    mime_type: str,
    size: int,
    sha256: str,
    sensitivity: str = "INTERNAL",
    status: str = "QUARANTINED",  # Default QUARANTINED — worker releases after clean scan
):
    file = File(
        owner_id=owner_id,
        filename=filename,
        stored_name=stored_name,
        mime_type=mime_type,
        size=size,
        sha256=sha256,
        sensitivity=sensitivity,
        status=status,
        risk_score=0,
    )
    db.add(file)
    db.commit()
    db.refresh(file)
    return file


def get_file(db: Session, file_id: str):
    return db.query(File).filter(File.id == file_id).first()


def list_files(db: Session, owner_id: Optional[str] = None):
    query = db.query(File)
    if owner_id:
        query = query.filter(File.owner_id == owner_id)
    return query.order_by(File.created_at.desc()).all()


def delete_file(db: Session, file_id: str):
    file = get_file(db, file_id)
    if file is None:
        return None
    db.delete(file)
    db.commit()
    return file


def update_risk(db: Session, file_id: str, risk_score: int, status: str):
    file = get_file(db, file_id)
    if file is None:
        return None
    # Use setattr to avoid Pylance Column assignment errors
    setattr(file, "risk_score", risk_score)
    setattr(file, "status", status)
    db.commit()
    db.refresh(file)
    return file


def create_share(
    db: Session,
    file_id: str,
    token_hash: str,
    recipient: str,
    expiry: datetime,
    downloads_left: int = 1,
    device_lock: bool = False,
    watermark: bool = True,
):
    share = Share(
        file_id=file_id,
        token_hash=token_hash,
        recipient=recipient,
        expiry=expiry,
        downloads_left=downloads_left,
        device_lock=device_lock,
        watermark=watermark,
        status="ACTIVE",
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


def get_share_by_token(db: Session, token_hash: str):
    return db.query(Share).filter(Share.token_hash == token_hash).first()


def update_share_downloads(db: Session, share_id: str):
    share = db.query(Share).filter(Share.id == share_id).first()
    if share:
        current = cast(int, share.downloads_left) or 0
        setattr(share, "downloads_left", current - 1)
        if current - 1 <= 0:
            setattr(share, "status", "EXHAUSTED")
        db.commit()
        db.refresh(share)
    return share
