from sqlalchemy.orm import Session

from app.models.alert import Alert


def create_alert(
    db: Session,
    type: str,
    severity: str,
    actor: str,
    score_delta: int,
    details: str,
):
    alert = Alert(
        type=type,
        severity=severity,
        actor=actor,
        score_delta=score_delta,
        details=details,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def list_alerts(db: Session, limit: int = 100, offset: int = 0):
    return (
        db.query(Alert)
        .order_by(Alert.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
