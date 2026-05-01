# ZT-SDX — Frontend ↔ Gateway API Contract

**Base URL:** `http://localhost:8000` (dev) — set via `GATEWAY_URL` in `.env`  
**All requests go to the Gateway API only. Never call internal services directly.**

---

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens are issued by `/login` and rotated via `/refresh`.  
Token lifetime: **15 minutes** (access), **8 hours** (refresh).

---

## Error Format

All errors follow this shape:

```json
{
  "detail": "Human readable message"
}
```

Validation errors (wrong field names / missing fields) return `422`:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Endpoints

---

### POST `/login`

Login with email and password.

**Request body (JSON):**

```json
{
  "email": "alice@acme.com",
  "password": "S3cur3P@ss!",
  "device_fingerprint": "fp_abc123xyz"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | ✅ | User email address |
| `password` | string | ✅ | User password |
| `device_fingerprint` | string | ❌ | Browser/device fingerprint for zero-trust tracking |

**Response `200`:**

```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "alice@acme.com",
    "role": "EMPLOYEE",
    "org_id": "uuid",
    "device_trusted": false
  }
}
```

**Errors:**
- `401` — Invalid credentials
- `403` — Account not activated / suspended

---

### POST `/verify-otp`

Verify MFA OTP after login triggers a challenge.

**Request body (JSON):**

```json
{
  "challenge_id": "abc123",
  "otp": "482910"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `challenge_id` | string | ✅ | Challenge ID from login response |
| `otp` | string | ✅ | 6-digit OTP code |

**Response `200`:**

```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "risk_floor": 10,
  "expires_in": 900
}
```

**Errors:**
- `401` — Invalid or expired OTP

---

### POST `/logout`

Revoke session and blacklist token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**No request body.**

**Response `200`:**

```json
{
  "message": "Logged out successfully"
}
```

---

### POST `/refresh`

Rotate access token using refresh token.

**Request body (JSON):**

```json
{
  "refresh_token": "eyJhbGci..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | ✅ | Refresh token from login |

**Response `200`:**

```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Errors:**
- `401` — Invalid or expired refresh token

---

### GET `/me`

Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200`:**

```json
{
  "id": "uuid",
  "email": "alice@acme.com",
  "role": "EMPLOYEE",
  "org_id": "uuid",
  "department_id": "uuid",
  "employee_code": "EMP001",
  "clearance_level": 1,
  "status": "ACTIVE"
}
```

---

### POST `/provision`

Provision a new employee. Admin only.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request body (JSON):**

```json
{
  "org_id": "uuid",
  "email": "bob@acme.com",
  "role_name": "EMPLOYEE",
  "department_name": "Engineering"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `org_id` | string (UUID) | ✅ | Organization UUID |
| `email` | string | ✅ | New employee email |
| `role_name` | string | ✅ | One of: `SUPER_ADMIN`, `SECURITY_ADMIN`, `DEPT_HEAD`, `MANAGER`, `EMPLOYEE`, `AUDITOR` |
| `department_name` | string | ✅ | Must match existing department: `Engineering`, `Finance`, `HR`, `Security`, `Legal`, `Operations` |

**Response `200`:**

```json
{
  "user_id": "uuid",
  "activation_code": "abc123xyz...",
  "expires_at": "2026-05-08T00:00:00Z",
  "message": "Employee provisioned. Share the activation code securely."
}
```

**Errors:**
- `400` — Email already registered

---

### POST `/activate`

Activate account using code from provisioning.

**No auth header needed.**

**Request body (JSON):**

```json
{
  "activation_code": "abc123xyz...",
  "password": "MyP@ss123!"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `activation_code` | string | ✅ | Code from provisioning response |
| `password` | string | ✅ | Password to set on the account |

**Response `200`:**

```json
{
  "message": "Account activated successfully. You can now log in."
}
```

**Errors:**
- `400` — Invalid or already used activation code
- `400` — Activation code has expired

---

### POST `/upload`

Upload a file. Triggers async DLP scan. File starts as `QUARANTINED` and is released to `ACTIVE` after a clean scan.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request body (multipart/form-data):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | file | ✅ | — | The file to upload |
| `sensitivity` | string | ❌ | `INTERNAL` | `PUBLIC` \| `INTERNAL` \| `CONFIDENTIAL` \| `SECRET` |

**Who can upload what:**

| Role | PUBLIC | INTERNAL | CONFIDENTIAL | SECRET |
|------|--------|----------|--------------|--------|
| EMPLOYEE | ✅ | ✅ | ❌ | ❌ |
| MANAGER | ✅ | ✅ | ❌ | ❌ |
| DEPT_HEAD | ✅ | ✅ | ✅ | ❌ |
| AUDITOR | ✅ | ✅ | ❌ | ❌ |
| SECURITY_ADMIN | ✅ | ✅ | ✅ | ✅ |
| SUPER_ADMIN | ✅ | ✅ | ✅ | ✅ |

**Every upload goes through:**
1. Policy check (role vs sensitivity)
2. AES-256-GCM encryption before storage in MinIO
3. SHA-256 digest stored for integrity verification
4. Async DLP scan (PAN, Aadhaar, SSN, API keys, passwords)
5. File released to `ACTIVE` only after clean scan

**Response `200`:**

```json
{
  "file": {
    "id": "uuid",
    "filename": "salary-sheet.xlsx",
    "stored_name": "uuid-salary-sheet.xlsx.enc",
    "sha256": "abc123...",
    "status": "QUARANTINED",
    "encrypted": true
  },
  "message": "Upload successful. DLP scan queued."
}
```

**Errors:**
- `400` — Invalid sensitivity value
- `401` — Invalid token
- `403` — Role not allowed to upload this sensitivity level
- `413` — File too large (max 100MB)
- `415` — File type not allowed (pdf, docx, xlsx, png, jpg only)
- `429` — Rate limit exceeded (30 uploads/min)

---

### GET `/files`

List all files for the current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200`:**

```json
{
  "files": [
    {
      "id": "uuid",
      "filename": "salary-sheet.xlsx",
      "size": 204800,
      "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "sensitivity": "INTERNAL",
      "status": "ACTIVE",
      "risk_score": 12,
      "sha256": "abc123...",
      "created_at": "2026-05-01T10:00:00Z"
    }
  ]
}
```

---

### GET `/files/{file_id}`

Get metadata for a single file.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Path params:**

| Param | Type | Description |
|-------|------|-------------|
| `file_id` | string (UUID) | File UUID |

**Response `200`:**

```json
{
  "id": "uuid",
  "filename": "salary-sheet.xlsx",
  "stored_name": "uuid-salary-sheet.xlsx",
  "size": 204800,
  "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "sha256": "abc123...",
  "sensitivity": "INTERNAL",
  "status": "ACTIVE",
  "risk_score": 12,
  "created_at": "2026-05-01T10:00:00Z"
}
```

**Errors:**
- `404` — File not found

---

### GET `/files/{file_id}/download`

Get a presigned download URL for a file. URL expires in 60 seconds.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200`:**

```json
{
  "id": "uuid",
  "filename": "salary-sheet.xlsx",
  "download_url": "http://minio:9000/files/uuid-salary-sheet.xlsx?X-Amz-Signature=...",
  "sha256": "abc123...",
  "watermark": "user-uuid|file-uuid|2026-05-01T10:00:00Z",
  "expires_in_seconds": 60
}
```

> **Note:** Frontend should redirect to `download_url` immediately. URL expires in 60 seconds.

**Errors:**
- `403` — Policy denied or file quarantined
- `404` — File not found

---

### POST `/shares`

Create a share link for a file.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request body (JSON):**

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

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file_id` | string (UUID) | ✅ | — | File to share |
| `recipient_email` | string | ✅ | — | Recipient email address |
| `expiry_hours` | integer | ❌ | `24` | Hours until link expires (1–720) |
| `max_downloads` | integer | ❌ | `1` | Max downloads allowed (1–100) |
| `device_lock` | boolean | ❌ | `false` | Lock to first device that opens it |
| `watermark` | boolean | ❌ | `true` | Inject watermark on download |

**Response `200`:**

```json
{
  "share_id": "uuid",
  "share_token": "abc123xyz...",
  "recipient": "vendor@external.com",
  "expiry": "2026-05-02T10:00:00Z",
  "max_downloads": 1,
  "device_lock": false,
  "watermark": true
}
```

> **Important:** `share_token` is only returned once. Store it or send it to the recipient immediately.

---

### GET `/shares/{share_token}`

Download a file via share link. No authentication required.

**No headers needed.**

**Path params:**

| Param | Type | Description |
|-------|------|-------------|
| `share_token` | string | Token from share creation response |

**Response `200`:**

```json
{
  "id": "uuid",
  "filename": "salary-sheet.xlsx",
  "download_url": "http://minio:9000/files/uuid-salary-sheet.xlsx?X-Amz-Signature=...",
  "sha256": "abc123...",
  "watermark": "vendor@external.com|share-uuid|2026-05-01T10:00:00Z",
  "expires_in_seconds": 60
}
```

**Errors:**
- `403` — Share expired / exhausted / revoked / file quarantined
- `404` — Share not found

---

### GET `/audit/events`

List audit log events. Intended for Security Officer role.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | `100` | Max events to return |
| `offset` | integer | `0` | Pagination offset |

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "action": "FILE_UPLOAD",
    "resource": "file-uuid",
    "hash": "abc123...",
    "prev_hash": "xyz789..."
  }
]
```

---

### GET `/audit/verify`

Verify the audit chain has not been tampered with.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200`:**

```json
{
  "valid": true,
  "total_logs": 42,
  "first_hash": "abc123...",
  "last_hash": "xyz789..."
}
```

If tampered:

```json
{
  "valid": false,
  "total_logs": 42,
  "first_hash": "abc123...",
  "last_hash": "xyz789...",
  "error": "Hash mismatch at log uuid"
}
```

---

### GET `/alerts`

List security alerts.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | `100` | Max alerts to return |
| `offset` | integer | `0` | Pagination offset |

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "type": "HIGH_RISK_FILE",
    "severity": "HIGH",
    "score_delta": 85,
    "details": "file_id=uuid risk_score=85",
    "created_at": "2026-05-01T10:00:00Z"
  }
]
```

---

### POST `/orgs`

Create a new organization. Auto-creates default departments.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request body (JSON):**

```json
{
  "name": "Acme Corp",
  "domain": "acme.com",
  "legal_name": "Acme Corporation Pvt Ltd",
  "industry": "Technology",
  "country": "IN",
  "size": 500
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | ✅ | — | Organization display name |
| `domain` | string | ✅ | — | Unique domain (e.g. `acme.com`) |
| `legal_name` | string | ❌ | null | Legal entity name |
| `industry` | string | ❌ | null | Industry sector |
| `country` | string | ❌ | `"IN"` | Country code |
| `size` | integer | ❌ | null | Number of employees |

**Response `200`:**

```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "domain": "acme.com",
  "country": "IN",
  "created_at": "2026-05-01T10:00:00Z",
  "message": "Organization created with default departments."
}
```

---

### GET `/orgs`

List all organizations.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200`:**

```json
[
  {
    "id": "uuid",
    "name": "Acme Corp",
    "domain": "acme.com",
    "industry": "Technology",
    "country": "IN",
    "created_at": "2026-05-01T10:00:00Z"
  }
]
```

---

### GET `/orgs/{org_id}`

Get organization details.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200`:**

```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "legal_name": "Acme Corporation Pvt Ltd",
  "domain": "acme.com",
  "industry": "Technology",
  "country": "IN",
  "size": 500,
  "created_at": "2026-05-01T10:00:00Z"
}
```

---

### GET `/orgs/{org_id}/departments`

List departments in an organization. Use this to populate the department dropdown when provisioning employees.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200`:**

```json
[
  { "id": "uuid", "name": "Engineering", "org_id": "uuid", "created_at": "..." },
  { "id": "uuid", "name": "Finance", "org_id": "uuid", "created_at": "..." },
  { "id": "uuid", "name": "HR", "org_id": "uuid", "created_at": "..." }
]
```

---

### POST `/orgs/{org_id}/departments`

Add a custom department to an organization.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request body (JSON):**

```json
{ "name": "Data Science" }
```

**Response `200`:**

```json
{ "id": "uuid", "name": "Data Science", "org_id": "uuid" }
```

---

### DELETE `/files/{file_id}`

Delete a file.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response `200`:**

```json
{ "id": "uuid", "message": "File deleted" }
```

**Errors:**
- `404` — File not found

---

## Status Codes Reference

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request (e.g. email already exists, invalid code) |
| `401` | Unauthenticated (missing or invalid token) |
| `403` | Forbidden (policy denied, account suspended, share exhausted) |
| `404` | Resource not found |
| `422` | Validation error — wrong field name or missing required field |
| `500` | Internal server error |

---

## File Status Values

| Status | Meaning |
|--------|---------|
| `ACTIVE` | File is clean and accessible |
| `QUARANTINED` | File flagged by DLP scan — not downloadable |
| `SCANNING` | DLP scan in progress |
| `BLOCKED` | Permanently blocked |

---

## Role Values

| Role | Privilege Level | Description |
|------|----------------|-------------|
| `SUPER_ADMIN` | 100 | Full system access |
| `SECURITY_ADMIN` | 90 | Audit, alerts, risk dashboards |
| `DEPT_HEAD` | 75 | Read/write own dept, external share |
| `MANAGER` | 60 | Read/write own dept |
| `EMPLOYEE` | 20 | Own files only |
| `AUDITOR` | 50 | Read-only audit access |
