from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.audit_service import create_log, list_logs


router = APIRouter(
    prefix="/audit",
    tags=["audit"],
)


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
    db: Session = Depends(get_db),
):
    logs = list_logs(db)

    return [
        {
            "id": str(log.id),
            "action": log.action,
            "resource": log.resource,
            "hash": log.hash,
            "prev_hash": log.prev_hash,
        }
        for log in logs
    ]