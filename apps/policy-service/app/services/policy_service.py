from sqlalchemy.orm import Session

from app.models.policy import Policy


def create_policy(
    db: Session,
    role: str,
    resource_sensitivity: list[str],
    device_trusted: bool,
    risk_score_lt: int,
    action: str,
):
    policy = Policy(
        role=role,
        resource_sensitivity=resource_sensitivity,
        device_trusted=device_trusted,
        risk_score_lt=risk_score_lt,
        action=action,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    return policy


def find_matching_policy(
    db: Session,
    role: str,
):
    return (
        db.query(Policy)
        .filter(Policy.role == role)
        .first()
    )