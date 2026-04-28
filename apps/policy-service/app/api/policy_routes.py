from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.engine.evaluator import evaluate_access

from app.services.policy_service import create_policy


router = APIRouter(
    prefix="/policy",
    tags=["policy"],
)


@router.post("/evaluate")
def evaluate(
    role: str,
    resource: str,
    action: str,
    clearance_level: int,
    risk_score: int,
    db: Session = Depends(get_db),
):
    return evaluate_access(
        db=db,
        role=role,
        resource=resource,
        action=action,
        clearance_level=clearance_level,
        risk_score=risk_score,
    )
    
@router.post("/seed")
def seed_policy(
    db: Session = Depends(get_db),
):
    policy = create_policy(
    db=db,
    role="ADMIN",
    resource_sensitivity=["FILE", "SECRET"],
    device_trusted=True,
    risk_score_lt=80,
    action="ALLOW",
)

    return {
    "id": str(policy.id),
    "role": policy.role,
    "resource_sensitivity": policy.resource_sensitivity,
    "device_trusted": policy.device_trusted,
    "risk_score_lt": policy.risk_score_lt,
    "action": policy.action,
    }