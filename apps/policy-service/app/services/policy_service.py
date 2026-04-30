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


def find_matching_policy(db: Session, role: str):
    """Find policy by role name string."""
    return (
        db.query(Policy)
        .filter(Policy.role == role)
        .first()
    )


def get_policy_by_id(db: Session, policy_id: str):
    """Find policy by UUID."""
    return db.query(Policy).filter(Policy.id == policy_id).first()


def list_policies(db: Session):
    return db.query(Policy).all()


def update_policy(db: Session, policy_id: str, **kwargs):
    """Update policy by UUID."""
    policy = get_policy_by_id(db, policy_id)
    if policy:
        for key, value in kwargs.items():
            setattr(policy, key, value)
        db.commit()
        db.refresh(policy)
    return policy


def delete_policy(db: Session, policy_id: str):
    """Delete policy by UUID."""
    policy = get_policy_by_id(db, policy_id)
    if policy:
        db.delete(policy)
        db.commit()
    return policy
