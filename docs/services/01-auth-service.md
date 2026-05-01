# Auth Service — Technical Deep Dive

**Port:** 8001 (internal: 8000)
**Stack:** FastAPI, PostgreSQL, Redis, Argon2, JWT (HS256)
**Responsibility:** Identity, authentication, session management, enterprise hierarchy

---

## What It Does

The auth service is the identity backbone of ZT-SDX. Every user, organization, department, and session lives here. It handles the full lifecycle from account creation to logout, including MFA, device tracking, and login risk scoring.

---

## Data Models

### User
Stores identity with enterprise hierarchy bindings:
- `email`, `password_hash` (Argon2)
- `role` (string: EMPLOYEE, MANAGER, DEPT_HEAD, SECURITY_ADMIN, SUPER_ADMIN, AUDITOR)
- `org_id`, `department_id`, `role_id` — FK references to hierarchy tables
- `employee_code`, `manager_id` — org structure
- `clearance_level`, `device_trust`, `risk_score`
- `mfa_enabled` (default: false — enabled by risk engine)
- `status`: ACTIVE | PENDING_ACTIVATION | SUSPENDED

### Organization
Tenant root. Every user belongs to an org. Auto-creates 6 default departments on creation.

### Department
Engineering, Finance, HR, Security, Legal, Operations (default). Custom departments can be added.

### Credentials
Separate from User. Holds `activation_code`, `activated` flag, `password_changed` flag. Used for the provisioning flow.

### Device
Tracks browser/device fingerprints per user. `trusted` flag set by admin. Used in login risk scoring.

### Session
Created on every login. Stores `ip`, `device_id`, `risk_score`, `expires_at`. Deleted on logout.

### Invitation
Created when an employee is provisioned. Has `activation_code` and `expires_at` (7 days). Marked `used=true` on activation.

---

## Endpoints

### POST /auth/register
Bootstrap path — creates a user directly with a role. Used for the first SUPER_ADMIN and for dev/testing. Bypasses the provisioning flow.

### POST /auth/login
The most complex endpoint. Full flow:

1. Look up user by email
2. Check status (PENDING_ACTIVATION, SUSPENDED → reject)
3. Check `password_hash` not empty (provisioned but not activated → reject)
4. Track failed attempts in Redis (`login_attempts:{user_id}`, 15-min TTL)
5. Verify Argon2 password hash
6. On failure: increment counter, lock account at 5 attempts (`status = SUSPENDED`)
7. On success: clear attempt counter
8. Register/update device fingerprint if provided
9. **Compute login risk score** from available signals:
   - `+15 per previous failed attempt` (max +45)
   - `+25 if device fingerprint sent but device not trusted`
   - `+10 if no device fingerprint at all`
10. Create Session record in DB
11. Issue JWT (15 min) + refresh token (8 hrs)
12. Store refresh token hash in Redis (`refresh:{hash}`, 8hr TTL)
13. **MFA decision:**
    - `risk >= 60` → DENY login entirely
    - `risk >= 30` OR `mfa_enabled=True` → return OTP challenge
    - `risk < 30` → return JWT directly

### POST /auth/verify-otp
Validates OTP from Redis. Pre-generated tokens are stored alongside the OTP so they're consistent. On success: cleans up all OTP keys, stores refresh hash, returns JWT.

### POST /auth/logout
- Sets `revoked_user:{user_id}` in Redis (15-min TTL matching token lifetime)
- Deletes all Session records for this user
- Any subsequent request with the old token hits `deps.py` → finds revoked key → 401

### POST /auth/refresh
- Validates refresh token hash exists in Redis
- Rotates: deletes old hash, issues new access + refresh token pair
- New refresh hash stored in Redis

### POST /auth/provision
Admin creates an employee account:
1. Creates User with `status=PENDING_ACTIVATION`, empty `password_hash`
2. Creates Credentials with `activation_code`
3. Creates Invitation with 7-day expiry
4. Returns `activation_code` — admin shares this out-of-band

### POST /auth/activate
Employee sets their password:
1. Finds Credentials by `activation_code` where `activated=false`
2. Checks Invitation not expired
3. Sets `password_hash = argon2(password)`
4. Sets `user.status = ACTIVE`
5. Marks credentials and invitation as used

### GET /auth/me
Returns full user profile. Protected by `get_current_user` dependency which:
1. Extracts Bearer token
2. Verifies JWT signature
3. Checks `revoked_user:{user_id}` in Redis
4. Checks `user.status != SUSPENDED`

---

## Security Mechanisms

### Argon2 Password Hashing
Industry-standard memory-hard hash. Resistant to GPU brute force. Used via `passlib[argon2]`.

### JWT (HS256)
Payload contains: `sub` (user_id), `email`, `role`, `org_id`, `session_id`, `risk_score`, `exp`.
Secret from `JWT_SECRET` env var. 15-minute lifetime.

### Refresh Token Rotation
Refresh tokens are opaque random strings. Only their SHA-256 hash is stored in Redis. On use, the old token is deleted and a new pair is issued. Prevents replay attacks.

### Login Lockout
5 failed attempts within 15 minutes → account suspended. Counter stored in Redis with 15-min TTL. Cleared on successful login.

### Token Revocation
Redis key `revoked_user:{id}` with 15-min TTL (matching token lifetime). Checked on every authenticated request. Effectively blacklists the token without storing the full JWT.

### Device Fingerprinting
Browser fingerprint stored per user. New devices get `trusted=false`. Contributes +25 to login risk score. Admin can mark devices as trusted.

---

## Connections

- **Called by:** Gateway API (all auth operations)
- **Calls:** Nothing (self-contained)
- **Reads/writes:** PostgreSQL (users, sessions, devices, credentials, invitations, orgs, departments)
- **Uses Redis for:** Refresh tokens, OTP challenges, login attempt counters, token revocation
