# Auth Service Specification — ZT-SDX

## Purpose

Auth-service owns identity, authentication, session trust, and token issuance.

It manages:

* registration
* login
* password hashing
* MFA / OTP
* session issuance
* refresh tokens
* logout / revoke
* device trust
* session anomaly signals
* password reset
* account lockout

Auth does NOT decide authorization.

Authorization belongs to policy-service.

Auth proves identity.

---

# 1. Ownership

Directory:

```text id="k7m2q5"
apps/auth-service/
```

Structure:

```text id="p4q8m1"
app/
├── api/
├── models/
├── services/
├── core/
├── security/
├── otp/
├── session/
├── device/
└── validators/
```

---

# 2. Core Data Ownership

Primary tables:

```text id="u1m7q4"
users
sessions
refresh_tokens
trusted_devices
login_attempts
password_resets
```

Primary storage:

PostgreSQL

Fast cache:

Redis

Use Redis for:

* OTP cache
* temporary lockouts
* rate limits
* hot session cache

---

# 3. Identity Model

User:

```json id="b8q1m6"
{
  "id": "uuid",
  "email": "user@example.com",
  "password_hash": "...",
  "role": "EMPLOYEE",
  "department": "Security",
  "clearance_level": 3,
  "device_trust": 80,
  "risk_score": 12,
  "mfa_enabled": true,
  "status": "ACTIVE",
  "created_at": "..."
}
```

Never store plaintext password.

Only salted hash.

Recommended:

* Argon2id
  or
* bcrypt

---

# 4. Registration Flow

Endpoint:

```text id="r5m2q8"
POST /register
```

Input:

```json id="c2q7m1"
{
  "email": "",
  "password": "",
  "role": "",
  "department": ""
}
```

Flow:

```text id="p7m1q5"
validate
↓
hash password
↓
insert user
↓
create trusted device baseline
↓
audit log
↓
return token / verify email step
```

---

# 5. Login Flow

Endpoint:

```text id="k4q8m2"
POST /login
```

Input:

```json id="m1q7r3"
{
  "email": "",
  "password": "",
  "device": {},
  "ip": ""
}
```

Flow:

```text id="t6m2q8"
validate credentials
↓
update login_attempts
↓
compute device trust
↓
send telemetry to risk-service
↓
risk score returned
↓
if score high → require MFA
↓
issue OTP
↓
verify OTP
↓
issue JWT + refresh token
↓
audit log
```

Possible outcomes:

```text id="w3q8m1"
SUCCESS
INVALID_CREDENTIALS
LOCKED
MFA_REQUIRED
DENIED_HIGH_RISK
```

---

# 6. MFA / OTP

Implement:

```text id="x7m1q4"
app/otp/
```

Store OTP in Redis:

Key:

```text id="q2m8r5"
otp:<user_id>
```

TTL:

```text id="n5q1m7"
300 sec
```

Attempts limited.

After verify → delete OTP.

Methods:

* email OTP
* authenticator app later

---

# 7. Session Layer

Implement:

```text id="g8m2q4"
app/session/
```

Session record:

```json id="r1q7m3"
{
  "session_id": "uuid",
  "user_id": "uuid",
  "device_id": "...",
  "issued_at": "...",
  "expires_at": "...",
  "revoked": false
}
```

JWT:

Short:

```text id="u4m8q2"
15 min
```

Refresh:

Long:

```text id="b7q1m5"
7–30 days
```

Rotate refresh tokens.

Never reuse.

---

# 8. Device Trust

Implement:

```text id="p3m7q1"
app/device/
```

Fingerprint:

Signals:

* browser fingerprint
* OS
* timezone
* IP history
* geolocation
* device UUID
* hardware hints

Trust score:

```text id="m6q2r4"
0–100
```

New device:

lower trust.

Known device:

higher trust.

Trust affects login flow.

---

# 9. Lockout Protection

Track:

* failed attempts
* burst attempts
* credential stuffing pattern

Actions:

```text id="t1m8q6"
captcha
temporary lock
MFA escalation
deny
```

Redis counters.

---

# 10. Password Reset

Flow:

```text id="v5q1m3"
request reset
↓
issue token
↓
TTL
↓
verify
↓
new hash
↓
revoke sessions
↓
audit
```

---

# 11. APIs

Public:

```text id="k8m2q5"
POST /register
POST /login
POST /verify-otp
POST /refresh
POST /forgot-password
POST /reset-password
```

Protected:

```text id="a1q7m4"
POST /logout
GET  /me
GET  /sessions
DELETE /sessions/{id}
```

Admin:

```text id="r4m8q2"
GET /users
PUT /users/{id}/status
POST /users/{id}/reset-mfa
```

---

# 12. Integrations

Policy:

* role lookup

Risk:

* telemetry send
* score receive

Audit:

* log every auth event

Worker:

* email OTP / notifications

---

# 13. Security Rules

Must:

* hash passwords
* rotate refresh tokens
* short-lived JWT
* OTP rate limit
* revoke compromised sessions
* device-aware auth
* audit everything

Never:

* plaintext passwords
* raw OTP storage
* long-lived access tokens
* trust client-side role claims

---

# 14. Initial Build Order

1. user ORM
2. create user CRUD
3. register endpoint
4. login endpoint
5. password hashing
6. JWT issue
7. OTP
8. refresh tokens
9. sessions
10. device trust
11. risk integration
