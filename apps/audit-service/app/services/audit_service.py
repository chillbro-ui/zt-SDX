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
    prev_hash = cast(str, last.hash) if last is not None else GENESIS_HASH

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


def list_logs(db: Session, limit: int = 100, offset: int = 0):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def verify_chain(db: Session):
    # Always verify the full chain in chronological order
    logs = db.query(AuditLog).order_by(AuditLog.created_at.asc()).all()

    if not logs:
        return {"valid": True, "total_logs": 0, "first_hash": None, "last_hash": None}

    first_hash = logs[0].hash
    last_hash = logs[-1].hash

    for i, log in enumerate(logs):
        expected_prev = GENESIS_HASH if i == 0 else logs[i - 1].hash

        if log.prev_hash != expected_prev:
            return {
                "valid": False,
                "total_logs": len(logs),
                "first_hash": first_hash,
                "last_hash": last_hash,
                "error": f"Chain broken at log {log.id} (index {i})",
            }

        computed = compute_hash(
            prev_hash=log.prev_hash,
            actor=log.actor,
            action=log.action,
            resource=log.resource,
            ip=log.ip,
            result=log.result,
        )

        if computed != log.hash:
            return {
                "valid": False,
                "total_logs": len(logs),
                "first_hash": first_hash,
                "last_hash": last_hash,
                "error": f"Hash mismatch at log {log.id} (index {i})",
            }

    return {
        "valid": True,
        "total_logs": len(logs),
        "first_hash": first_hash,
        "last_hash": last_hash,
    }
