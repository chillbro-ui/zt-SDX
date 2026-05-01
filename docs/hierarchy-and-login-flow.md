# ZT-SDX — Enterprise Hierarchy & Login Flow

## 1. Hierarchy Structure

```
Platform (ZT-SDX)
└── Organization (e.g. Acme Corp)
    ├── SUPER_ADMIN       privilege: 100  — full system access
    ├── SECURITY_ADMIN    privilege: 90   — audit, alerts, risk dashboards
    ├── DEPT_HEAD         privilege: 75   — read/write own dept, external share
    ├── MANAGER           privilege: 60   — read/write own dept
    ├── EMPLOYEE          privilege: 20   — own files only
    └── AUDITOR           privilege: 50   — read-only audit access
```

---

## 2. How SUPER_ADMIN Sets Up the System

### Step 1 — SUPER_ADMIN registers (first time only)

```
POST /auth/register
{
  "email": "admin@acme.com",
  "password": "SecurePass!",
  "role": "SUPER_ADMIN",
  "department": "security"
}
```

This is the bootstrap path — used once to create the first admin.
After this, all users are provisioned through the hierarchy.

---

### Step 2 — Create the Organization

```
POST /orgs
Authorization: Bearer <admin_token>
{
  "name": "Acme Corp",
  "domain": "acme.com",
  "country": "IN"
}
```

Returns `org_id`. Auto-creates 6 default departments:
`Engineering`, `Finance`, `HR`, `Security`, `Legal`, `Operations`

---

### Step 3 — Provision Employees

```
POST /provision
Authorization: Bearer <admin_token>
{
  "org_id": "uuid",
  "email": "bob@acme.com",
  "role_name": "EMPLOYEE",
  "department_name": "Engineering"
}
```

Returns `activation_code`. Admin shares this with the employee.

---

### Step 4 — Employee Activates Account

```
POST /activate
{
  "activation_code": "abc123...",
  "password": "MyPassword!"
}
```

Account status changes from `PENDING_ACTIVATION` → `ACTIVE`.

---

## 3. Login Flow

```
POST /login
{
  "email": "bob@acme.com",
  "password": "MyPassword!",
  "device_fingerprint": "fp_abc123"   ← optional
}
```

### Case A — MFA disabled (mfa_enabled = false)

```json
{
  "otp_required": false,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "bob@acme.com",
    "role": "EMPLOYEE",
    "org_id": "uuid",
    "device_trusted": false
  }
}
```

Frontend receives JWT → stores it → uses it for all requests.

---

### Case B — MFA enabled (triggered by risk engine or manual override)

When the risk service returns `MFA_REQUIRED`, or when `mfa_enabled=True` is set manually on the user:

```json
{
  "otp_required": true,
  "challenge_id": "abc123xyz",
  "otp": "482910",
  "expires_in_seconds": 300,
  "user": {
    "id": "uuid",
    "email": "bob@acme.com",
    "role": "EMPLOYEE"
  }
}
```

Frontend shows OTP input screen. User enters the OTP.

```
POST /verify-otp
{
  "challenge_id": "abc123xyz",
  "otp": "482910"
}
```

Returns same JWT response as Case A.

> **Note:** In production the OTP would be sent via email/SMS.
> Returned here for demo purposes only.
>
> **MFA trigger:** `mfa_enabled=False` by default. The risk engine (ML team)
> sets this to `True` dynamically based on behavioral signals — new device,
> unusual geo, bulk downloads, odd hours. Admin can also force it manually.

---

## 4. How Frontend Determines the Dashboard

The JWT payload contains the user's `role`. After login, the frontend reads it:

```javascript
// Decode JWT (or use /me endpoint)
const user = await fetch('/me', { headers: { Authorization: `Bearer ${token}` } })
const { role, org_id } = await user.json()

// Route to correct dashboard
switch (role) {
  case 'SUPER_ADMIN':    navigate('/dashboard/admin')     break
  case 'SECURITY_ADMIN': navigate('/dashboard/security')  break
  case 'DEPT_HEAD':      navigate('/dashboard/dept-head') break
  case 'MANAGER':        navigate('/dashboard/manager')   break
  case 'EMPLOYEE':       navigate('/dashboard/employee')  break
  case 'AUDITOR':        navigate('/dashboard/audit')     break
}
```

---

## 5. What Each Dashboard Shows

| Role | Dashboard Access |
|------|-----------------|
| `SUPER_ADMIN` | All users, all orgs, all files, all audit logs, all alerts, policy management, provisioning |
| `SECURITY_ADMIN` | Audit logs, alerts, risk scores, user sessions, read-only on all files |
| `DEPT_HEAD` | Own department files, share management, provision employees in own dept |
| `MANAGER` | Own department files, upload/download, share within org |
| `EMPLOYEE` | Own files only, upload/download, create share links |
| `AUDITOR` | Read-only audit log viewer, chain verification |

---

## 6. What's in the JWT

```json
{
  "sub": "user-uuid",
  "email": "bob@acme.com",
  "role": "EMPLOYEE",
  "org_id": "org-uuid",
  "session_id": "session-uuid",
  "exp": 1777607000
}
```

- `sub` — user ID, used to fetch full profile from `/me`
- `role` — used by frontend to route to correct dashboard
- `org_id` — used to scope data queries to the user's organization
- `session_id` — used for session revocation on logout
- `exp` — token expires in 15 minutes, refresh with `/refresh`

---

## 7. Token Lifecycle

```
Login → access_token (15 min) + refresh_token (8 hrs)
    ↓
Access token expires
    ↓
POST /refresh { refresh_token }
    → New access_token + new refresh_token (rotation)
    ↓
Refresh token expires (8 hrs)
    → User must log in again
    ↓
Logout
    → POST /logout
    → Token blacklisted in Redis (15 min TTL)
    → All sessions deleted from DB
    → Any request with old token → 401
```

---

## 8. Full Provisioning Flow (SUPER_ADMIN perspective)

```
1. Register as SUPER_ADMIN
2. Create organization → get org_id
3. View departments → GET /orgs/{org_id}/departments
4. Provision employee → POST /provision
   → Returns activation_code
5. Share activation_code with employee (out of band)
6. Employee activates → POST /activate
7. Employee logs in → POST /login
8. Employee gets JWT with role=EMPLOYEE
9. Frontend routes to /dashboard/employee
```

---

## 9. API Endpoints Summary

| Action | Endpoint | Who |
|--------|----------|-----|
| Bootstrap admin | `POST /auth/register` | First-time setup |
| Create org | `POST /orgs` | SUPER_ADMIN |
| List departments | `GET /orgs/{id}/departments` | SUPER_ADMIN |
| Add department | `POST /orgs/{id}/departments` | SUPER_ADMIN |
| Provision employee | `POST /provision` | SUPER_ADMIN / SECURITY_ADMIN |
| Activate account | `POST /activate` | Employee (no auth needed) |
| Login | `POST /login` | Any user |
| Verify OTP | `POST /verify-otp` | Any user (if MFA enabled) |
| Get profile | `GET /me` | Any authenticated user |
| Refresh token | `POST /refresh` | Any authenticated user |
| Logout | `POST /logout` | Any authenticated user |
