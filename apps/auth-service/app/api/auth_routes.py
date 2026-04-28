from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.security.password import hash_password
from app.services.user_service import create_user, get_user_by_email

from app.security.deps import get_current_user
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(
    email: str,
    password: str,
    role: str,
    department: str,
    db: Session = Depends(get_db),
):
    existing = get_user_by_email(db, email)

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = create_user(
        db=db,
        email=email,
        password_hash=hash_password(password),
        role=role,
        department=department,
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "department": user.department,
        "status": user.status,
    }
    
from app.security.password import verify_password
from app.security.token import create_access_token


@router.post("/login")
def login(
    email: str,
    password: str,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        password,
        str(user.password_hash),
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }
    
    
@router.get("/me")
def me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
    }