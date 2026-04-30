from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User


def create_user(
    db: Session,
    email: str,
    password_hash: str,
    role: str,
    department: str,
    clearance_level: int = 1,
    org_id: Optional[str] = None,
    department_id: Optional[str] = None,
    role_id: Optional[str] = None,
    employee_code: Optional[str] = None,
    manager_id: Optional[str] = None,
):
    user = User(
        email=email,
        password_hash=password_hash,
        role=role,
        department=department,
        clearance_level=clearance_level,
        org_id=org_id,
        department_id=department_id,
        role_id=role_id,
        employee_code=employee_code,
        manager_id=manager_id,
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


def get_user_by_employee_code(
    db: Session,
    employee_code: str,
):
    return (
        db.query(User)
        .filter(User.employee_code == employee_code)
        .first()
    )


def list_users(db: Session, org_id: Optional[str] = None):
    query = db.query(User)
    if org_id:
        query = query.filter(User.org_id == org_id)
    return query.all()


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


def update_user_status(
    db: Session,
    user_id: str,
    status: str,
):
    user = get_user_by_id(db, user_id)
    if user:
        user.status = status
        db.commit()
        db.refresh(user)
    return user


def update_user_manager(
    db: Session,
    user_id: str,
    manager_id: str,
):
    user = get_user_by_id(db, user_id)
    if user:
        user.manager_id = manager_id
        db.commit()
        db.refresh(user)
    return user
