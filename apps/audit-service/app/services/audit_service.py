from typing import cast

from sqlalchemy.orm import Session

from app.crypto.chain import compute_hash
from app.models.audit_log import AuditLog


GENESIS_HASH = "GENESIS"


def get_last_log(db: Session):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .first()
    )


def create_log(
    db: Session,
    actor: str,
    action: str,
    resource: str,
    ip: str,
    result: str,
):
    last = get_last_log(db)

    prev_hash = (
        cast(str, last.hash)
        if last is not None
        else GENESIS_HASH
    )

    current_hash = compute_hash(
        prev_hash=prev_hash,
        actor=actor,
        action=action,
        resource=resource,
        ip=ip,
        result=result,
    )

    log = AuditLog(
        actor=actor,
        action=action,
        resource=resource,
        ip=ip,
        result=result,
        prev_hash=prev_hash,
        hash=current_hash,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def list_logs(db: Session):
    return db.query(AuditLog).all()