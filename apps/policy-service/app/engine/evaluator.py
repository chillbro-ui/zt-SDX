from typing import cast
from sqlalchemy.orm import Session

from app.services.policy_service import find_matching_policy


def evaluate_access(
    db: Session,
    role: str,
    resource: str,
    action: str,
    clearance_level: int,
    risk_score: int,
):
    policy = find_matching_policy(db, role)

    if policy is None:
        return {
            "decision": "DENY",
            "reason": "NO_POLICY",
        }

    allowed = cast(list[str], policy.resource_sensitivity)
    risk_limit = cast(int, policy.risk_score_lt)

    if resource not in allowed:
        return {
            "decision": "DENY",
            "reason": "RESOURCE_DENIED",
        }

    if risk_score >= risk_limit:
        return {
            "decision": "MFA_REQUIRED",
            "reason": "HIGH_RISK",
        }

    return {
        "decision": "ALLOW",
        "reason": "POLICY_MATCH",
    }