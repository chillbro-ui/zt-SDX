from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.engine.evaluator import evaluate_access
from app.services.policy_service import (
    create_policy,
    delete_policy,
    find_matching_policy,
    list_policies,
)

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/evaluate")
def evaluate(
    role: str,
    resource: str,
    action: str,
    clearance_level: int,
    risk_score: int,
    device_trusted: bool = False,
    db: Session = Depends(get_db),
):
    return evaluate_access(
        db=db,
        role=role,
        resource=resource,
        action=action,
        clearance_level=clearance_level,
        risk_score=risk_score,
        device_trusted=device_trusted,
    )


@router.post("/seed")
def seed_policies(db: Session = Depends(get_db)):
    """
    Seed default policies for all roles.
    Safe to call multiple times — skips roles that already have a policy.
    """
    from app.services.policy_service import find_matching_policy

    defaults = [
        {
            "role": "SUPER_ADMIN",
            "resource_sensitivity": ["FILE", "SECRET", "CONFIDENTIAL", "INTERNAL", "PUBLIC"],
            "device_trusted": False,
            "risk_score_lt": 90,
            "action": "ALLOW",
        },
        {
            "role": "SECURITY_ADMIN",
            "resource_sensitivity": ["FILE", "SECRET", "CONFIDENTIAL", "INTERNAL", "PUBLIC"],
            "device_trusted": False,
            "risk_score_lt": 80,
            "action": "ALLOW",
        },
        {
            "role": "DEPT_HEAD",
            "resource_sensitivity": ["FILE", "CONFIDENTIAL", "INTERNAL", "PUBLIC"],
            "device_trusted": False,
            "risk_score_lt": 60,
            "action": "ALLOW",
        },
        {
            "role": "MANAGER",
            "resource_sensitivity": ["FILE", "INTERNAL", "PUBLIC"],
            "device_trusted": False,
            "risk_score_lt": 50,
            "action": "ALLOW",
        },
        {
            "role": "EMPLOYEE",
            "resource_sensitivity": ["FILE", "INTERNAL", "PUBLIC"],
            "device_trusted": False,
            "risk_score_lt": 40,
            "action": "ALLOW",
        },
        {
            "role": "AUDITOR",
            "resource_sensitivity": ["FILE", "INTERNAL", "PUBLIC"],
            "device_trusted": False,
            "risk_score_lt": 60,
            "action": "ALLOW",
        },
    ]

    created = []
    skipped = []

    for p in defaults:
        existing = find_matching_policy(db, p["role"])
        if existing:
            skipped.append(p["role"])
            continue
        policy = create_policy(
            db=db,
            role=p["role"],
            resource_sensitivity=p["resource_sensitivity"],
            device_trusted=p["device_trusted"],
            risk_score_lt=p["risk_score_lt"],
            action=p["action"],
        )
        created.append(p["role"])

    return {"created": created, "skipped": skipped}


@router.get("/")
def get_policies(db: Session = Depends(get_db)):
    policies = list_policies(db)
    return {
        "policies": [
            {
                "id": str(p.id),
                "role": p.role,
                "resource_sensitivity": p.resource_sensitivity,
                "device_trusted": p.device_trusted,
                "risk_score_lt": p.risk_score_lt,
                "action": p.action,
            }
            for p in policies
        ]
    }


@router.delete("/{policy_id}")
def remove_policy(policy_id: str, db: Session = Depends(get_db)):
    policy = delete_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return {"id": policy_id, "message": "Policy deleted"}
