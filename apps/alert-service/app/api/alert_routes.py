from datetime import datetime
from typing import Optional, cast

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.alert_service import create_alert, list_alerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/create")
def make_alert(
    type: str,
    severity: str,
    actor: str,
    score_delta: int,
    details: str,
    db: Session = Depends(get_db),
):
    alert = create_alert(
        db=db,
        type=type,
        severity=severity,
        actor=actor,
        score_delta=score_delta,
        details=details,
    )

    return {
        "id": str(alert.id),
        "type": cast(str, alert.type),
        "severity": cast(str, alert.severity),
        "score_delta": cast(int, alert.score_delta),
        "details": cast(str, alert.details),
        "created_at": cast(datetime, alert.created_at).isoformat() if cast(Optional[datetime], alert.created_at) else None,
    }


@router.get("/")
def get_alerts(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    alerts = list_alerts(db, limit=limit, offset=offset)

    return [
        {
            "id": str(a.id),
            "type": cast(str, a.type),
            "severity": cast(str, a.severity),
            "score_delta": cast(int, a.score_delta),
            "details": cast(str, a.details),
            "created_at": cast(datetime, a.created_at).isoformat() if cast(Optional[datetime], a.created_at) else None,
        }
        for a in alerts
    ]
