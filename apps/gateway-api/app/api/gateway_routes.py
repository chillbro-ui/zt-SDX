from fastapi import APIRouter, Depends, File as UploadFileType, HTTPException, Request, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.schemas import (
    ActivateRequest,
    AddDepartmentRequest,
    CreateOrgRequest,
    CreateShareRequest,
    LoginRequest,
    ProvisionRequest,
    RefreshRequest,
    VerifyOtpRequest,
)
from app.clients import alert_client, audit_client, auth_client, file_client, org_client, policy_client, risk_client
from app.clients.queue_client import enqueue
from app.security.rate_limit import check_rate_limit
from app.security.roles import require_min_privilege, require_roles

router = APIRouter(tags=["gateway"])

bearer = HTTPBearer()


def get_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    return credentials.credentials


# ─── Auth ─────────────────────────────────────────────────────────────────────

@router.post("/login", summary="Login with email + password")
async def login(request: Request, body: LoginRequest):
    # Rate limit: 10 login attempts per minute per IP
    check_rate_limit(request, key_prefix="login", limit=10, window=60)
    return await auth_client.login(
        email=body.email,
        password=body.password,
        device_fingerprint=body.device_fingerprint,
    )


@router.post("/verify-otp", summary="Verify MFA OTP")
async def verify_otp(request: Request, body: VerifyOtpRequest):
    # Rate limit: 5 OTP attempts per minute per IP
    check_rate_limit(request, key_prefix="otp", limit=5, window=60)
    return await auth_client.verify_otp(
        challenge_id=body.challenge_id,
        otp=body.otp,
    )


@router.post("/logout", summary="Logout — revoke session")
async def logout(token: str = Depends(get_token)):
    return await auth_client.logout(token=token)


@router.post("/refresh", summary="Rotate access token using refresh token")
async def refresh_token(body: RefreshRequest):
    return await auth_client.refresh_token(refresh_token=body.refresh_token)


@router.get("/me", summary="Get current user profile")
async def get_current_user(token: str = Depends(get_token)):
    return await auth_client.me(token)


# ─── Provisioning — SUPER_ADMIN / SECURITY_ADMIN only ────────────────────────

@router.post("/provision", summary="Provision a new employee (admin only)")
async def provision_employee(
    body: ProvisionRequest,
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN"])),
):
    return await auth_client.provision_employee(
        org_id=body.org_id,
        email=body.email,
        role_name=body.role_name,
        department_name=body.department_name,
    )


@router.post("/activate", summary="Activate account using code from provisioning email")
async def activate_account(body: ActivateRequest):
    return await auth_client.activate_account(
        activation_code=body.activation_code,
        password=body.password,
    )


# ─── Files ────────────────────────────────────────────────────────────────────

@router.post("/upload", summary="Upload a file (multipart/form-data)")
async def upload(
    request: Request,
    file: UploadFile = UploadFileType(...),
    sensitivity: str = "INTERNAL",
    token: str = Depends(get_token),
):
    """
    sensitivity: PUBLIC | INTERNAL | CONFIDENTIAL | SECRET (default: INTERNAL)
    """
    check_rate_limit(request, key_prefix="upload", limit=30, window=60)

    user = await auth_client.me(token)
    if "id" not in user:
        raise HTTPException(status_code=401, detail="Invalid token")

    valid_sensitivities = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "SECRET"]
    sensitivity = sensitivity.upper()
    if sensitivity not in valid_sensitivities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sensitivity '{sensitivity}'. Must be one of: {', '.join(valid_sensitivities)}",
        )

    # ── Score FILE_UPLOAD event via risk-service ──────────────────────────────
    # Use the live user risk score for the policy check, not a hardcoded 0.
    risk_result = await risk_client.score_event(
        user_id=user["id"],
        event="FILE_UPLOAD",
        ip=request.client.host if request.client else None,
        sensitivity=sensitivity,
        token=token,
    )
    user_risk_score = int(risk_result.get("risk_score", 0))
    # ─────────────────────────────────────────────────────────────────────────

    # Policy check — uses live risk score from risk-service
    decision = await policy_client.evaluate(
        role=user["role"],
        resource=sensitivity,
        action="UPLOAD",
        clearance_level=user.get("clearance_level", 1),
        risk_score=user_risk_score,
    )

    if decision["decision"] != "ALLOW":
        raise HTTPException(
            status_code=403,
            detail={
                **decision,
                "risk_score": user_risk_score,
                "message": f"Your role '{user['role']}' cannot upload {sensitivity} files (risk score: {user_risk_score}).",
            },
        )

    content = await file.read()

    uploaded = await file_client.upload(
        owner_id=user["id"],
        filename=file.filename or "unknown",
        content=content,
        content_type=file.content_type or "application/octet-stream",
        sensitivity=sensitivity,
    )

    if "id" not in uploaded:
        raise HTTPException(status_code=400, detail=uploaded.get("detail", "File upload failed"))

    enqueue({
        "file_id": uploaded["id"],
        "owner_id": user["id"],
        "stored_name": uploaded["stored_name"],
        "sensitivity": sensitivity,
        "action": "SCAN",
    })

    await audit_client.log(
        actor=user["id"],
        action="FILE_UPLOAD",
        resource=uploaded["id"],
        ip=request.client.host if request.client else "gateway",
        result="SUCCESS",
    )

    return {
        "file": uploaded,
        "risk_score": user_risk_score,
        "message": "Upload successful. DLP scan queued.",
    }


@router.get("/files", summary="List files for current user")
async def list_files(token: str = Depends(get_token)):
    user = await auth_client.me(token)
    return await file_client.list_files(owner_id=user["id"])


@router.get("/files/{file_id}", summary="Get file metadata")
async def get_file(file_id: str, token: str = Depends(get_token)):
    await auth_client.me(token)
    return await file_client.get_file(file_id=file_id)


@router.get("/files/{file_id}/download", summary="Download a file (decrypted, streamed)")
async def download_file(request: Request, file_id: str, token: str = Depends(get_token)):
    user = await auth_client.me(token)

    file_meta = await file_client.get_file(file_id=file_id)
    file_sensitivity = file_meta.get("sensitivity", "INTERNAL") if isinstance(file_meta, dict) else "INTERNAL"

    # ── Score FILE_DOWNLOAD event via risk-service ────────────────────────────
    # This updates the user's running risk profile AND gives us the live score
    # to pass to the policy engine — replacing the stale file-level risk_score.
    risk_result = await risk_client.score_event(
        user_id=user["id"],
        event="FILE_DOWNLOAD",
        ip=request.client.host if request.client else None,
        sensitivity=file_sensitivity,
        token=token,
    )
    user_risk_score = int(risk_result.get("risk_score", 0))
    # ─────────────────────────────────────────────────────────────────────────

    decision = await policy_client.evaluate(
        role=user["role"],
        resource=file_sensitivity,
        action="DOWNLOAD",
        clearance_level=user.get("clearance_level", 1),
        risk_score=user_risk_score,
    )

    if decision["decision"] != "ALLOW":
        raise HTTPException(
            status_code=403,
            detail={
                **decision,
                "risk_score": user_risk_score,
            },
        )

    result = await file_client.download_file(file_id=file_id, user_id=user["id"])

    await audit_client.log(
        actor=user["id"],
        action="FILE_DOWNLOAD",
        resource=file_id,
        ip=request.client.host if request.client else "gateway",
        result="SUCCESS",
    )

    return result


# ─── Shares ───────────────────────────────────────────────────────────────────

@router.post("/shares", summary="Create a share link for a file")
async def create_share(request: Request, body: CreateShareRequest, token: str = Depends(get_token)):
    user = await auth_client.me(token)

    # ── Score SHARE_CREATED event via risk-service ────────────────────────────
    risk_result = await risk_client.score_event(
        user_id=user["id"],
        event="SHARE_CREATED",
        ip=request.client.host if request.client else None,
        token=token,
    )
    user_risk_score = int(risk_result.get("risk_score", 0))

    # Block share creation if user risk is CRITICAL
    if risk_result.get("recommended_action") == "DENY":
        raise HTTPException(
            status_code=403,
            detail=f"Share creation blocked. User risk score {user_risk_score} is too high.",
        )
    # ─────────────────────────────────────────────────────────────────────────

    result = await file_client.create_share(
        file_id=body.file_id,
        recipient_email=body.recipient_email,
        expiry_hours=body.expiry_hours,
        max_downloads=body.max_downloads,
        device_lock=body.device_lock,
        watermark=body.watermark,
    )

    await audit_client.log(
        actor=user["id"],
        action="SHARE_CREATED",
        resource=body.file_id,
        ip=request.client.host if request.client else "gateway",
        result="SUCCESS",
    )

    return result


@router.get("/shares/{share_token}", summary="Download file via share link (no auth required)")
async def download_via_share(share_token: str):
    result = await file_client.download_via_share(share_token=share_token)

    await audit_client.log(
        actor="anonymous",
        action="SHARE_DOWNLOAD",
        resource=share_token,
        ip="gateway",
        result="SUCCESS",
    )

    return result


# ─── Risk — SECURITY_ADMIN / SUPER_ADMIN only ────────────────────────────────

@router.get("/risk/user/{user_id}", summary="Get risk profile for a user")
async def get_user_risk_profile(
    user_id: str,
    token: str = Depends(get_token),
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN"])),
):
    """
    Returns the current risk profile for any user.
    Proxies to risk-service GET /risk/user/{user_id}/profile.
    """
    return await risk_client.get_user_risk(user_id=user_id, token=token)


@router.get("/risk/alerts", summary="Get risk alerts (all users)")
async def get_risk_alerts(
    token: str = Depends(get_token),
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN"])),
):
    """
    Returns recent risk alerts from risk-service.
    """
    from app.clients.config import RISK_URL
    import httpx
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{RISK_URL}/risk/alerts",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception:
        return []


# ─── Audit — SECURITY_ADMIN / AUDITOR / SUPER_ADMIN only ─────────────────────

@router.get("/audit/events", summary="List audit log events")
async def get_audit_events(
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN", "AUDITOR"])),
):
    return await audit_client.list_events(limit=limit, offset=offset)


@router.get("/audit/verify", summary="Verify audit chain integrity")
async def verify_audit_chain(
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN", "AUDITOR"])),
):
    return await audit_client.verify_chain()


# ─── Alerts — SECURITY_ADMIN / SUPER_ADMIN only ───────────────────────────────

@router.get("/alerts", summary="List security alerts")
async def get_alerts(
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN"])),
):
    return await alert_client.list_alerts(limit=limit, offset=offset)


# ─── Organizations — SUPER_ADMIN only ────────────────────────────────────────

@router.post("/orgs", summary="Create a new organization")
async def create_org(
    body: CreateOrgRequest,
    user: dict = Depends(require_roles(["SUPER_ADMIN"])),
):
    return await org_client.create_org(
        name=body.name,
        domain=body.domain,
        legal_name=body.legal_name,
        industry=body.industry,
        country=body.country,
        size=body.size,
    )


@router.get("/orgs", summary="List all organizations")
async def list_orgs(
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN"])),
):
    return await org_client.list_orgs()


@router.get("/orgs/{org_id}", summary="Get organization details")
async def get_org(
    org_id: str,
    user: dict = Depends(require_min_privilege(60)),
):
    return await org_client.get_org(org_id)


@router.get("/orgs/{org_id}/departments", summary="List departments in an organization")
async def get_departments(
    org_id: str,
    user: dict = Depends(require_min_privilege(20)),
):
    return await org_client.get_departments(org_id)


@router.post("/orgs/{org_id}/departments", summary="Add a department to an organization")
async def add_department(
    org_id: str,
    body: AddDepartmentRequest,
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN"])),
):
    return await org_client.add_department(org_id=org_id, name=body.name)


# ─── File Delete ──────────────────────────────────────────────────────────────

@router.delete("/files/{file_id}", summary="Delete a file")
async def delete_file(request: Request, file_id: str, token: str = Depends(get_token)):
    user = await auth_client.me(token)
    result = await file_client.delete_file(file_id=file_id)

    await audit_client.log(
        actor=user["id"],
        action="FILE_DELETE",
        resource=file_id,
        ip=request.client.host if request.client else "gateway",
        result="SUCCESS",
    )

    return result
