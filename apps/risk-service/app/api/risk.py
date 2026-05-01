import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.enums import RiskLevel, RecommendedAction
from app.security.deps import get_current_user
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk", tags=["risk-profile"])


class RiskProfileResponse(BaseModel):
    user_id: str
    risk_score: float
    risk_level: RiskLevel
    recommended_action: RecommendedAction
    score_count: int

    class Config:
        from_attributes = True


@router.get("/user/{user_id}/profile", response_model=RiskProfileResponse)
async def get_user_risk(
    user_id: str,
    _caller: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current risk profile for a user.

    Called by: gateway-api, policy-service, auth-service
    Auth: Bearer JWT required
    """
    try:
        svc = RiskService(db)
        profile = await svc.get_profile(user_id)
    except Exception as exc:
        logger.error(f"get_user_risk failed for user={user_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve risk profile")

    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No risk profile found for user {user_id}",
        )

    return RiskProfileResponse(
        user_id=profile.user_id,
        risk_score=profile.risk_score,
        risk_level=profile.risk_level,
        recommended_action=profile.recommended_action,
        score_count=profile.score_count,
    )
