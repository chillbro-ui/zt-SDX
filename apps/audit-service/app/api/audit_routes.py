from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.audit_service import create_log, list_logs, verify_chain

router = APIRouter(prefix="/audit", tags=["audit"])


@router.post("/log")
def log_event(
    actor: str,
    action: str,
    resource: str,
    ip: str,
    result: str,
    db: Session = Depends(get_db),
):
    log = create_log(
        db=db,
        actor=actor,
        action=action,
        resource=resource,
        ip=ip,
        result=result,
    )
    return {
        "id": str(log.id),
        "hash": log.hash,
        "prev_hash": log.prev_hash,
    }


@router.get("/logs")
def get_logs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    logs = list_logs(db, limit=limit, offset=offset)
    return [
        {
            "id": str(log.id),
            "actor": str(log.actor) if log.actor else None,
            "action": log.action,
            "resource": log.resource,
            "ip": log.ip,
            "result": log.result,
            "hash": log.hash,
            "prev_hash": log.prev_hash,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/verify")
def verify_audit_chain(db: Session = Depends(get_db)):
    result = verify_chain(db)
    return {
        "valid": result["valid"],
        "total_logs": result["total_logs"],
        "first_hash": result["first_hash"],
        "last_hash": result["last_hash"],
        "error": result.get("error"),
    }
