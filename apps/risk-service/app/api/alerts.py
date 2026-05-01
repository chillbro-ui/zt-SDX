import logging

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.enums import AlertType, AlertSeverity
from app.models.alert import Alert
from app.security.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["alerts"])


class AlertResponse(BaseModel):
    id: str
    user_id: str
    alert_type: AlertType
    severity: AlertSeverity
    score_delta: float
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/alerts", response_model=list[AlertResponse])
async def get_alerts(
    user_id: str | None = Query(default=None, description="Filter by user ID"),
    limit: int = Query(default=50, ge=1, le=200),
    _caller: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns recent risk alerts, optionally filtered by user.

    Called by: gateway-api (security dashboard), audit-service
    Auth: Bearer JWT required
    """
    try:
        query = db.query(Alert).order_by(Alert.created_at.desc())
        if user_id:
            query = query.filter(Alert.user_id == user_id)
        alerts = query.limit(limit).all()
    except Exception as exc:
        logger.error(f"get_alerts failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")

    return [
        AlertResponse(
            id=a.id,
            user_id=a.user_id,
            alert_type=a.alert_type,
            severity=a.severity,
            score_delta=a.score_delta,
            description=a.description,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.get("/alerts/{user_id}", response_model=list[AlertResponse])
async def get_user_alerts(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    _caller: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns risk alerts for a specific user.

    Called by: gateway-api, policy-service
    Auth: Bearer JWT required
    """
    try:
        alerts = (
            db.query(Alert)
            .filter(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc())
            .limit(limit)
            .all()
        )
    except Exception as exc:
        logger.error(f"get_user_alerts failed for user={user_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve user alerts")

    return [
        AlertResponse(
            id=a.id,
            user_id=a.user_id,
            alert_type=a.alert_type,
            severity=a.severity,
            score_delta=a.score_delta,
            description=a.description,
            created_at=a.created_at,
        )
        for a in alerts
    ]
