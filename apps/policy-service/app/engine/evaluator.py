from typing import cast, Optional

from sqlalchemy.orm import Session

from app.services.policy_service import find_matching_policy


def evaluate_access(
    db: Session,
    role: str,
    resource: str,
    action: str,
    clearance_level: int,
    risk_score: int,
    device_trusted: bool = False,
    ip: Optional[str] = None,       # Reserved for geo-based checks (not yet implemented)
    time_utc: Optional[str] = None, # Reserved for time-window checks (not yet implemented)
):
    """
    Evaluate access based on role policy.

    Decision order:
    1. No policy found → DENY
    2. Resource not in allowed list → DENY
    3. Risk score >= threshold → MFA_REQUIRED
    4. Policy requires trusted device but device is not trusted → MFA_REQUIRED
    5. All checks pass → ALLOW
    """
    policy = find_matching_policy(db, role)

    if policy is None:
        return {"decision": "DENY", "reason": "NO_POLICY"}

    allowed_resources = cast(list[str], policy.resource_sensitivity)
    risk_limit = cast(int, policy.risk_score_lt)

    if resource not in allowed_resources:
        return {"decision": "DENY", "reason": "RESOURCE_DENIED"}

    if risk_score >= risk_limit:
        return {"decision": "MFA_REQUIRED", "reason": "HIGH_RISK"}

    if bool(policy.device_trusted) and not device_trusted:
        return {"decision": "MFA_REQUIRED", "reason": "UNTRUSTED_DEVICE"}

    return {"decision": "ALLOW", "reason": "POLICY_MATCH"}
