import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.cache import rdb
from app.core.db import get_db
from app.models.credentials import Credentials
from app.models.device import Device
from app.models.invitation import Invitation
from app.models.session import Session as SessionModel
from app.models.user import User
from app.security.deps import get_current_user
from app.security.password import hash_password, verify_password
from app.security.token import create_access_token, create_refresh_token, verify_access_token
from app.services.user_service import create_user, get_user_by_email, get_user_by_id

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
        raise HTTPException(status_code=400, detail="Email already registered")

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


@router.post("/login")
def login(
    request: Request,
    email: str,
    password: str,
    device_fingerprint: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.status == "PENDING_ACTIVATION":
        raise HTTPException(
            status_code=403,
            detail="Account not activated. Check your email for activation instructions.",
        )

    if user.status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Guard against empty password_hash (provisioned but not yet activated)
    if not user.password_hash:
        raise HTTPException(status_code=403, detail="Account not activated.")

    if not verify_password(password, str(user.password_hash)):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Resolve client IP
    client_ip = request.client.host if request.client else "unknown"

    # Register or update device
    device_id = None
    device_trusted = False
    if device_fingerprint:
        device = db.query(Device).filter(
            Device.user_id == user.id,
            Device.fingerprint == device_fingerprint,
        ).first()

        if not device:
            device = Device(
                user_id=user.id,
                fingerprint=device_fingerprint,
                trusted=False,
                last_seen=datetime.now(timezone.utc),
            )
            db.add(device)
        else:
            device.last_seen = datetime.now(timezone.utc)

        db.commit()
        db.refresh(device)
        device_id = str(device.id)
        device_trusted = bool(device.trusted)

    # Risk score placeholder — risk service will update this
    risk_score = 10

    # Create session
    session = SessionModel(
        user_id=user.id,
        ip=client_ip,
        device_id=device_id,
        risk_score=risk_score,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Issue JWT
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "org_id": str(user.org_id) if user.org_id else None,
        "session_id": str(session.id),
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id), "session_id": str(session.id)})

    # Store refresh token hash in Redis (8hr TTL)
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    rdb.setex(f"refresh:{refresh_hash}", 28800, str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "role": user.role,
            "org_id": str(user.org_id) if user.org_id else None,
            "device_trusted": device_trusted,
        },
    }


@router.post("/verify-otp")
def verify_otp(
    challenge_id: str,
    otp: str,
    db: Session = Depends(get_db),
):
    # Placeholder — OTP delivery (TOTP/SMS/Email) is out of scope for this sprint
    # challenge_id maps to a Redis key set during login MFA trigger
    stored = rdb.get(f"otp:{challenge_id}")
    if not stored or stored != otp:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    rdb.delete(f"otp:{challenge_id}")

    # Retrieve user_id stored alongside OTP
    user_id = rdb.get(f"otp_user:{challenge_id}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired")

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "org_id": str(user.org_id) if user.org_id else None,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id)})

    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    rdb.setex(f"refresh:{refresh_hash}", 28800, str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "risk_floor": 10,
        "expires_in": 900,
    }


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Blacklist the JTI in Redis for the token lifetime (15 min)
    # The token itself is passed via Bearer header — deps already validated it
    # We store user_id → revoked marker; full JTI blacklist needs token passed in body
    rdb.setex(f"revoked_user:{str(current_user.id)}", 900, "1")

    # Delete all active sessions for this user
    db.query(SessionModel).filter(SessionModel.user_id == current_user.id).delete()
    db.commit()

    return {"message": "Logged out successfully"}


@router.post("/refresh")
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    # Validate refresh token exists in Redis
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    user_id = rdb.get(f"refresh:{refresh_hash}")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = get_user_by_id(db, user_id)
    if not user or user.status != "ACTIVE":
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Rotate: delete old, issue new
    rdb.delete(f"refresh:{refresh_hash}")

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "org_id": str(user.org_id) if user.org_id else None,
    }
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token({"sub": str(user.id)})

    new_refresh_hash = hashlib.sha256(new_refresh.encode()).hexdigest()
    rdb.setex(f"refresh:{new_refresh_hash}", 28800, str(user.id))

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": 900,
    }


@router.post("/provision")
def provision_employee(
    org_id: str,
    email: str,
    role_name: str,
    department_name: str,
    db: Session = Depends(get_db),
):
    existing = get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    activation_code = secrets.token_urlsafe(32)

    user = User(
        email=email,
        password_hash="",  # Set on activation
        org_id=org_id,
        role=role_name,
        department=department_name,
        status="PENDING_ACTIVATION",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    creds = Credentials(
        user_id=user.id,
        activation_code=activation_code,
        activated=False,
        password_changed=False,
    )
    db.add(creds)

    invitation = Invitation(
        org_id=org_id,
        email=email,
        activation_code=activation_code,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        used=False,
    )
    db.add(invitation)
    db.commit()

    return {
        "user_id": str(user.id),
        "activation_code": activation_code,
        "expires_at": cast(datetime, invitation.expires_at).isoformat(),
        "message": "Employee provisioned. Share the activation code securely.",
    }


@router.post("/activate")
def activate_account(
    activation_code: str,
    password: str,
    db: Session = Depends(get_db),
):
    creds = db.query(Credentials).filter(
        Credentials.activation_code == activation_code,
        Credentials.activated == False,
    ).first()

    if not creds:
        raise HTTPException(status_code=400, detail="Invalid or already used activation code")

    # Check invitation not expired
    invitation = db.query(Invitation).filter(
        Invitation.activation_code == activation_code,
        Invitation.used == False,
    ).first()

    if not invitation:
        raise HTTPException(status_code=400, detail="Invitation not found or already used")

    expires_at = cast(datetime, invitation.expires_at)
    if expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Activation code has expired")

    user = get_user_by_id(db, creds.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Set password and activate
    user.password_hash = hash_password(password)
    user.status = "ACTIVE"
    creds.activated = True
    creds.password_changed = True
    invitation.used = True

    db.commit()

    return {"message": "Account activated successfully. You can now log in."}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "org_id": str(current_user.org_id) if current_user.org_id else None,
        "department_id": str(current_user.department_id) if current_user.department_id else None,
        "employee_code": current_user.employee_code,
        "clearance_level": current_user.clearance_level,
        "status": current_user.status,
    }


@router.post("/devices/register")
def register_device(
    device_fingerprint: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    device = db.query(Device).filter(
        Device.user_id == current_user.id,
        Device.fingerprint == device_fingerprint,
    ).first()

    if not device:
        device = Device(
            user_id=current_user.id,
            fingerprint=device_fingerprint,
            trusted=False,
            last_seen=datetime.now(timezone.utc),
        )
        db.add(device)
        db.commit()
        db.refresh(device)
    else:
        device.last_seen = datetime.now(timezone.utc)
        db.commit()

    return {
        "device_id": str(device.id),
        "trusted": device.trusted,
        "last_seen": device.last_seen.isoformat(),
    }


@router.get("/devices")
def list_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    devices = db.query(Device).filter(Device.user_id == current_user.id).all()

    return {
        "devices": [
            {
                "id": str(d.id),
                "fingerprint": d.fingerprint,
                "trusted": d.trusted,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            }
            for d in devices
        ]
    }
