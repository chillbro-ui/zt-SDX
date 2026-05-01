from fastapi import APIRouter, Depends, File as UploadFileType, HTTPException, UploadFile
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

router = APIRouter(tags=["gateway"])

# Bearer token extractor — frontend sends:  Authorization: Bearer <token>
bearer = HTTPBearer()


def get_token(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    return credentials.credentials


# ─── Auth ─────────────────────────────────────────────────────────────────────

@router.post("/login", summary="Login with email + password")
async def login(body: LoginRequest):
    """
    Frontend sends JSON body:
    ```json
    { "email": "alice@acme.com", "password": "S3cur3P@ss!", "device_fingerprint": "fp_abc" }
    ```
    Returns access_token + refresh_token.
    """
    return await auth_client.login(
        email=body.email,
        password=body.password,
        device_fingerprint=body.device_fingerprint,
    )


@router.post("/verify-otp", summary="Verify MFA OTP")
async def verify_otp(body: VerifyOtpRequest):
    """
    Frontend sends JSON body:
    ```json
    { "challenge_id": "...", "otp": "482910" }
    ```
    """
    return await auth_client.verify_otp(
        challenge_id=body.challenge_id,
        otp=body.otp,
    )


@router.post("/logout", summary="Logout — revoke session")
async def logout(token: str = Depends(get_token)):
    """
    Frontend sends:  Authorization: Bearer <access_token>
    """
    return await auth_client.logout(token=token)


@router.post("/refresh", summary="Rotate access token using refresh token")
async def refresh_token(body: RefreshRequest):
    """
    Frontend sends JSON body:
    ```json
    { "refresh_token": "..." }
    ```
    """
    return await auth_client.refresh_token(refresh_token=body.refresh_token)


@router.get("/me", summary="Get current user profile")
async def get_current_user(token: str = Depends(get_token)):
    """
    Frontend sends:  Authorization: Bearer <access_token>
    """
    return await auth_client.me(token)


# ─── Provisioning ─────────────────────────────────────────────────────────────

@router.post("/provision", summary="Provision a new employee (admin only)")
async def provision_employee(body: ProvisionRequest, token: str = Depends(get_token)):
    """
    Frontend sends JSON body:
    ```json
    {
      "org_id": "uuid",
      "email": "bob@acme.com",
      "role_name": "EMPLOYEE",
      "department_name": "Engineering"
    }
    ```
    """
    return await auth_client.provision_employee(
        org_id=body.org_id,
        email=body.email,
        role_name=body.role_name,
        department_name=body.department_name,
    )


@router.post("/activate", summary="Activate account using code from provisioning email")
async def activate_account(body: ActivateRequest):
    """
    Frontend sends JSON body:
    ```json
    { "activation_code": "...", "password": "MyP@ss123!" }
    ```
    """
    return await auth_client.activate_account(
        activation_code=body.activation_code,
        password=body.password,
    )


# ─── Files ────────────────────────────────────────────────────────────────────

@router.post("/upload", summary="Upload a file (multipart/form-data)")
async def upload(
    file: UploadFile = UploadFileType(...),
    token: str = Depends(get_token),
):
    """
    Frontend sends multipart/form-data with field name `file`.
    Authorization: Bearer <access_token>
    """
    user = await auth_client.me(token)

    if "id" not in user:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Policy check — use risk_score=0 for upload (risk is scored async by worker after upload)
    decision = await policy_client.evaluate(
        role=user["role"],
        resource="FILE",
        action="UPLOAD",
        clearance_level=1,
        risk_score=0,
    )

    if decision["decision"] != "ALLOW":
        raise HTTPException(status_code=403, detail=decision)

    content = await file.read()

    uploaded = await file_client.upload(
        owner_id=user["id"],
        filename=file.filename or "unknown",
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )

    if "id" not in uploaded:
        raise HTTPException(status_code=400, detail=uploaded.get("detail", "File upload failed"))

    enqueue({
        "file_id": uploaded["id"],
        "owner_id": user["id"],
        "stored_name": uploaded["stored_name"],
        "action": "SCAN",
    })

    await audit_client.log(
        actor=user["id"],
        action="FILE_UPLOAD",
        resource=uploaded["id"],
        ip="gateway",
        result="SUCCESS",
    )

    return {"file": uploaded, "message": "Upload successful. DLP scan queued."}


@router.get("/files", summary="List files for current user")
async def list_files(token: str = Depends(get_token)):
    """
    Authorization: Bearer <access_token>
    """
    user = await auth_client.me(token)
    return await file_client.list_files(owner_id=user["id"])


@router.get("/files/{file_id}", summary="Get file metadata")
async def get_file(file_id: str, token: str = Depends(get_token)):
    """
    Authorization: Bearer <access_token>
    """
    await auth_client.me(token)
    return await file_client.get_file(file_id=file_id)


@router.get("/files/{file_id}/download", summary="Download a file (returns presigned URL)")
async def download_file(file_id: str, token: str = Depends(get_token)):
    """
    Authorization: Bearer <access_token>
    Returns a presigned MinIO URL valid for 60 seconds + watermark metadata.
    """
    user = await auth_client.me(token)

    # Get file metadata first to use its stored risk_score
    file_meta = await file_client.get_file(file_id=file_id)
    stored_risk = file_meta.get("risk_score", 0) if isinstance(file_meta, dict) else 0

    decision = await policy_client.evaluate(
        role=user["role"],
        resource="FILE",
        action="DOWNLOAD",
        clearance_level=1,
        risk_score=stored_risk,
    )

    if decision["decision"] != "ALLOW":
        raise HTTPException(status_code=403, detail=decision)

    result = await file_client.download_file(file_id=file_id, user_id=user["id"])

    await audit_client.log(
        actor=user["id"],
        action="FILE_DOWNLOAD",
        resource=file_id,
        ip="gateway",
        result="SUCCESS",
    )

    return result


# ─── Shares ───────────────────────────────────────────────────────────────────

@router.post("/shares", summary="Create a share link for a file")
async def create_share(body: CreateShareRequest, token: str = Depends(get_token)):
    """
    Frontend sends JSON body:
    ```json
    {
      "file_id": "uuid",
      "recipient_email": "vendor@external.com",
      "expiry_hours": 24,
      "max_downloads": 1,
      "device_lock": false,
      "watermark": true
    }
    ```
    Returns share_token — only shown once, store it securely.
    """
    user = await auth_client.me(token)

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
        ip="gateway",
        result="SUCCESS",
    )

    return result


@router.get("/shares/{share_token}", summary="Download file via share link (no auth required)")
async def download_via_share(share_token: str):
    """
    No Authorization header needed — token is in the URL path.
    """
    result = await file_client.download_via_share(share_token=share_token)

    await audit_client.log(
        actor="anonymous",
        action="SHARE_DOWNLOAD",
        resource=share_token,
        ip="gateway",
        result="SUCCESS",
    )

    return result


# ─── Audit ────────────────────────────────────────────────────────────────────

@router.get("/audit/events", summary="List audit log events (security officer only)")
async def get_audit_events(
    limit: int = 100,
    offset: int = 0,
    token: str = Depends(get_token),
):
    await auth_client.me(token)
    return await audit_client.list_events(limit=limit, offset=offset)


@router.get("/audit/verify", summary="Verify audit chain integrity")
async def verify_audit_chain(token: str = Depends(get_token)):
    await auth_client.me(token)
    return await audit_client.verify_chain()


# ─── Alerts ───────────────────────────────────────────────────────────────────

@router.get("/alerts", summary="List security alerts")
async def get_alerts(
    limit: int = 100,
    offset: int = 0,
    token: str = Depends(get_token),
):
    await auth_client.me(token)
    return await alert_client.list_alerts(limit=limit, offset=offset)


# ─── Organizations ────────────────────────────────────────────────────────────

@router.post("/orgs", summary="Create a new organization")
async def create_org(body: CreateOrgRequest, token: str = Depends(get_token)):
    """
    Frontend sends JSON body:
    ```json
    { "name": "Acme Corp", "domain": "acme.com", "country": "IN" }
    ```
    Auto-creates default departments: Engineering, Finance, HR, Security, Legal, Operations.
    """
    await auth_client.me(token)
    return await org_client.create_org(
        name=body.name,
        domain=body.domain,
        legal_name=body.legal_name,
        industry=body.industry,
        country=body.country,
        size=body.size,
    )


@router.get("/orgs", summary="List all organizations")
async def list_orgs(token: str = Depends(get_token)):
    await auth_client.me(token)
    return await org_client.list_orgs()


@router.get("/orgs/{org_id}", summary="Get organization details")
async def get_org(org_id: str, token: str = Depends(get_token)):
    await auth_client.me(token)
    return await org_client.get_org(org_id)


@router.get("/orgs/{org_id}/departments", summary="List departments in an organization")
async def get_departments(org_id: str, token: str = Depends(get_token)):
    await auth_client.me(token)
    return await org_client.get_departments(org_id)


@router.post("/orgs/{org_id}/departments", summary="Add a department to an organization")
async def add_department(org_id: str, body: AddDepartmentRequest, token: str = Depends(get_token)):
    await auth_client.me(token)
    return await org_client.add_department(org_id=org_id, name=body.name)


# ─── File Delete ──────────────────────────────────────────────────────────────

@router.delete("/files/{file_id}", summary="Delete a file")
async def delete_file(file_id: str, token: str = Depends(get_token)):
    """
    Authorization: Bearer <access_token>
    """
    user = await auth_client.me(token)
    result = await file_client.delete_file(file_id=file_id)

    await audit_client.log(
        actor=user["id"],
        action="FILE_DELETE",
        resource=file_id,
        ip="gateway",
        result="SUCCESS",
    )

    return result
