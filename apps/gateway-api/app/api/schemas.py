from typing import Optional
from pydantic import BaseModel, Field


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address", json_schema_extra={"example": "alice@acme.com"})
    password: str = Field(..., description="User password", json_schema_extra={"example": "S3cur3P@ss!"})
    device_fingerprint: Optional[str] = Field(
        default=None,
        description="Browser/device fingerprint string for zero-trust device tracking",
        json_schema_extra={"example": "fp_abc123xyz"},
    )


class VerifyOtpRequest(BaseModel):
    challenge_id: str = Field(..., description="Challenge ID returned from login MFA trigger")
    otp: str = Field(..., description="6-digit OTP code", json_schema_extra={"example": "482910"})


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token issued at login")


class ProvisionRequest(BaseModel):
    org_id: str = Field(..., description="UUID of the organization")
    email: str = Field(..., description="New employee email", json_schema_extra={"example": "bob@acme.com"})
    role_name: str = Field(
        ...,
        description="One of: SUPER_ADMIN, SECURITY_ADMIN, DEPT_HEAD, MANAGER, EMPLOYEE, AUDITOR",
        json_schema_extra={"example": "EMPLOYEE"},
    )
    department_name: str = Field(
        ...,
        description="Must match an existing department in the org",
        json_schema_extra={"example": "Engineering"},
    )


class ActivateRequest(BaseModel):
    activation_code: str = Field(..., description="Code from the provisioning email")
    password: str = Field(
        ...,
        description="New password to set on activation",
        json_schema_extra={"example": "MyP@ss123!"},
    )


# ─── Organizations ────────────────────────────────────────────────────────────

class CreateOrgRequest(BaseModel):
    name: str = Field(..., description="Organization display name", json_schema_extra={"example": "Acme Corp"})
    domain: str = Field(..., description="Unique org domain", json_schema_extra={"example": "acme.com"})
    legal_name: Optional[str] = Field(default=None, json_schema_extra={"example": "Acme Corporation Pvt Ltd"})
    industry: Optional[str] = Field(default=None, json_schema_extra={"example": "Technology"})
    country: str = Field(default="IN", json_schema_extra={"example": "IN"})
    size: Optional[int] = Field(default=None, description="Number of employees", json_schema_extra={"example": 500})


class AddDepartmentRequest(BaseModel):
    name: str = Field(..., description="Department name", json_schema_extra={"example": "Data Science"})


# ─── Shares ───────────────────────────────────────────────────────────────────

class CreateShareRequest(BaseModel):
    file_id: str = Field(..., description="UUID of the file to share")
    recipient_email: str = Field(..., description="Recipient email address", json_schema_extra={"example": "vendor@external.com"})
    expiry_hours: int = Field(default=24, ge=1, le=720, description="Link expiry in hours (1–720)")
    max_downloads: int = Field(default=1, ge=1, le=100, description="Max number of downloads allowed")
    device_lock: bool = Field(default=False, description="Lock link to first device that opens it")
    watermark: bool = Field(default=True, description="Inject watermark on download")
