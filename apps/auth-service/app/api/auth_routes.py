import hashlib
import logging
import os
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.clients.risk_client import score_login_event
from app.core.cache import rdb
from app.core.config import settings
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

logger = logging.getLogger(__name__)

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
async def login(
    request: Request,
    email: str,
    password: str,
    device_fingerprint: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, email)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check account status
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

    # ── Login attempt tracking ────────────────────────────────────────────────
    attempt_key = f"login_attempts:{str(user.id)}"
    attempts = int(rdb.get(attempt_key) or 0)

    if not verify_password(password, str(user.password_hash)):
        # Increment failed attempts
        new_count = attempts + 1
        rdb.setex(attempt_key, 900, str(new_count))  # 15 min window

        if new_count >= settings.MAX_LOGIN_ATTEMPTS:
            user.status = "SUSPENDED"
            db.commit()
            raise HTTPException(
                status_code=403,
                detail=f"Account locked after {settings.MAX_LOGIN_ATTEMPTS} failed attempts. Contact your administrator.",
            )

        # ── Report LOGIN_FAILED to risk-service (fire-and-forget) ──────────
        try:
            await score_login_event(
                user_id=str(user.id),
                event="LOGIN_FAILED",
                ip=request.client.host if request.client else None,
                is_new_fingerprint=not bool(device_fingerprint),
            )
        except Exception as exc:
            logger.warning(f"Risk scoring LOGIN_FAILED failed (non-fatal): {exc}")
        # ─────────────────────────────────────────────────────────────────────

        remaining = settings.MAX_LOGIN_ATTEMPTS - new_count
        raise HTTPException(
            status_code=401,
            detail=f"Invalid credentials. {remaining} attempt(s) remaining before lockout.",
        )

    # Successful login — clear failed attempts
    rdb.delete(attempt_key)

    # Resolve client IP
    client_ip = request.client.host if request.client else "unknown"

    # Register or update device
    device_id = None
    device_trusted = False
    is_new_device = False
    if device_fingerprint:
        device = db.query(Device).filter(
            Device.user_id == user.id,
            Device.fingerprint == device_fingerprint,
        ).first()

        if not device:
            is_new_device = True
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

    # ── Score this login event via risk-service ───────────────────────────────
    # Determine which event type to send based on device state
    risk_event_type = "NEW_DEVICE_LOGIN" if is_new_device else "LOGIN_SUCCESS"

    # Device trust: trusted=100, untrusted=50, unknown=40
    device_trust_score: float | None = None
    if device_fingerprint:
        device_trust_score = float(settings.TRUSTED_DEVICE_SCORE) if device_trusted else 50.0
    else:
        device_trust_score = 40.0  # no fingerprint = unknown device

    try:
        risk_result = await score_login_event(
            user_id=str(user.id),
            event=risk_event_type,
            ip=client_ip,
            device_id=device_id,
            device_trust=device_trust_score,
            is_new_fingerprint=is_new_device,
        )
    except Exception as exc:
        logger.warning(f"Risk scoring failed during login (fail-open): {exc}")
        risk_result = {"risk_score": 0, "recommended_action": "ALLOW", "level": "LOW"}

    login_risk = int(risk_result.get("risk_score", 0))
    # ─────────────────────────────────────────────────────────────────────────

    # Create session with risk score from risk-service
    session = SessionModel(
        user_id=user.id,
        ip=client_ip,
        device_id=device_id,
        risk_score=login_risk,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Issue JWT — embed risk_score so downstream services can use it
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "org_id": str(user.org_id) if user.org_id else None,
        "session_id": str(session.id),
        "risk_score": login_risk,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": str(user.id), "session_id": str(session.id)})

    # Store refresh token hash in Redis (8hr TTL)
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    rdb.setex(f"refresh:{refresh_hash}", 28800, str(user.id))

    # ── MFA / Deny decision driven by risk-service score ─────────────────────
    mfa_threshold = int(os.getenv("RISK_MFA_THRESHOLD", "30"))
    deny_threshold = int(os.getenv("RISK_DENY_THRESHOLD", "60"))

    if login_risk >= deny_threshold:
        raise HTTPException(
            status_code=403,
            detail=f"Login blocked. Risk score {login_risk} exceeds threshold. Contact your administrator.",
        )

    trigger_mfa = user.mfa_enabled or (login_risk >= mfa_threshold)

    if trigger_mfa:
        otp = str(random.randint(100000, 999999))
        challenge_id = secrets.token_urlsafe(16)
        otp_ttl = settings.OTP_EXPIRY_SECONDS

        rdb.setex(f"otp:{challenge_id}", otp_ttl, otp)
        rdb.setex(f"otp_user:{challenge_id}", otp_ttl, str(user.id))
        rdb.setex(f"otp_access:{challenge_id}", otp_ttl, access_token)
        rdb.setex(f"otp_refresh:{challenge_id}", otp_ttl, refresh_token)

        return {
            "otp_required": True,
            "challenge_id": challenge_id,
            "otp": otp,  # Demo only — production sends via email/SMS
            "expires_in_seconds": otp_ttl,
            "risk_score": login_risk,
            "risk_level": risk_result.get("level", "LOW"),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
            },
        }

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
        "otp_required": False,
        "risk_score": login_risk,
        "risk_level": risk_result.get("level", "LOW"),
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
    stored = rdb.get(f"otp:{challenge_id}")
    if not stored or stored != otp:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    user_id = rdb.get(f"otp_user:{challenge_id}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Session expired")

    # Retrieve pre-generated tokens
    access_token = rdb.get(f"otp_access:{challenge_id}")
    refresh_token = rdb.get(f"otp_refresh:{challenge_id}")

    if not access_token or not refresh_token:
        raise HTTPException(status_code=401, detail="Session expired — please log in again")

    # Clean up OTP keys
    rdb.delete(f"otp:{challenge_id}")
    rdb.delete(f"otp_user:{challenge_id}")
    rdb.delete(f"otp_access:{challenge_id}")
    rdb.delete(f"otp_refresh:{challenge_id}")

    # Store refresh token hash for rotation
    refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    rdb.setex(f"refresh:{refresh_hash}", 28800, user_id)

    user = get_user_by_id(db, user_id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 900,
        "user": {
            "id": str(user.id) if user else user_id,
            "email": user.email if user else None,
            "role": user.role if user else None,
            "org_id": str(user.org_id) if user and user.org_id else None,
        },
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
