from sqlalchemy.orm import Session

from app.models.user import User


def create_user(
    db: Session,
    email: str,
    password_hash: str,
    role: str,
    department: str,
    clearance_level: int = 1,
):
    user = User(
        email=email,
        password_hash=password_hash,
        role=role,
        department=department,
        clearance_level=clearance_level,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_email(
    db: Session,
    email: str,
):
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def get_user_by_id(
    db: Session,
    user_id,
):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def list_users(db: Session):
    return db.query(User).all()


def delete_user(
    db: Session,
    user_id,
):
    user = get_user_by_id(db, user_id)

    if not user:
        return None

    db.delete(user)
    db.commit()

    return user