import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.clients import audit_client
from app.core.db import get_db
from app.core.enums import RiskLevel, RecommendedAction
from app.features.schemas import TelemetryEvent
from app.security.deps import get_service_or_user
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["scoring"])


class ScoreResponse(BaseModel):
    risk_score: float
    level: RiskLevel
    recommended_action: RecommendedAction
    rule_score: float
    ml_score: float
    fired_rules: list[dict]


@router.post("/score", response_model=ScoreResponse)
async def score_event(
    event: TelemetryEvent,
    _caller: dict = Depends(get_service_or_user),
    db: Session = Depends(get_db),
):
    """
    Main scoring endpoint. Accepts a telemetry event from any upstream
    service and returns the user's current risk score and recommended action.

    Called by: gateway-api, worker-service
    Auth: Bearer JWT (service token or user token — both accepted)
    """
    try:
        svc = RiskService(db)
        result = await svc.process_event(event)
    except Exception as exc:
        logger.error(f"score_event failed for user={event.user_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Risk scoring failed")

    # Audit the scoring decision (fire-and-forget)
    await audit_client.log_event(
        actor=event.user_id,
        action="RISK_SCORED",
        resource=f"event:{event.event}",
        ip=event.ip or "unknown",
        result=result.recommended_action.value,
    )

    return ScoreResponse(
        risk_score=result.final_score,
        level=result.level,
        recommended_action=result.recommended_action,
        rule_score=result.rule_score,
        ml_score=result.ml_score,
        fired_rules=result.fired_rules,
    )
