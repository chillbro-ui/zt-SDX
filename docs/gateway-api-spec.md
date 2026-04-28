# Gateway API Specification — ZT-SDX

## Purpose

Gateway API is the single public backend entrypoint.

Frontend talks only to gateway.

Gateway routes internally to services.

```text id="t3n7q1"
Frontend
   ↓
Gateway API
   ├── Auth Service
   ├── Policy Service
   ├── File Service
   ├── Risk Service
   ├── Audit Service
   └── Worker Service
```

Gateway owns:

* request routing
* auth middleware
* token verification
* request validation
* response normalization
* rate limiting
* aggregation endpoints
* logging
* websocket fanout (later)

Gateway does NOT own business logic.

---

# 1. Ownership

Directory:

```text id="m8q2r5"
apps/gateway-api/
```

Internal structure:

```text id="q4p7n1"
app/
├── api/
├── clients/
├── middleware/
├── core/
├── utils/
└── schemas/
```

---

# 2. Core Responsibilities

## Request Proxying

Example:

Frontend:

```text id="y1r6m3"
POST /api/auth/login
```

Gateway forwards:

```text id="p7k2q4"
auth-service/login
```

Returns normalized response.

---

## Authentication Verification

Gateway validates JWT before forwarding protected requests.

Adds:

```text id="v6m1p8"
X-User-ID
X-Role
X-Risk-Score
```

headers internally.

---

## Authorization Precheck

Optional quick deny:

Example:

```text id="n3q7m2"
expired token
blocked user
missing scopes
```

Reject before internal call.

---

## Aggregation

Can merge responses.

Example:

Dashboard:

Gateway collects:

* user summary
* recent files
* alerts
* risk score

Returns one payload.

Frontend makes one call.

---

# 3. Internal Clients

Build:

```text id="c8p1m6"
app/clients/
```

Clients:

```text id="f2r7n4"
auth_client.py
policy_client.py
file_client.py
risk_client.py
audit_client.py
worker_client.py
```

Example:

```python id="u5q2m8"
POST auth-service/login
GET file-service/files
GET risk-service/user/{id}
```

Use async HTTP.

Recommended:

* httpx.AsyncClient

---

# 4. Routes

Public:

```text id="x9m4q1"
/api/auth/login
/api/auth/register
/api/auth/verify-otp
```

Protected:

```text id="b3r8n5"
/api/files/*
/api/shares/*
/api/alerts/*
/api/audit/*
/api/users/*
/api/policies/*
```

Admin:

```text id="r6p2m7"
/api/admin/*
```

Health:

```text id="w1q5n9"
/health
/routes
```

---

# 5. Middleware

Build:

```text id="g7m3p1"
app/middleware/
```

Need:

## request_id.py

Add request UUID.

Traceability.

---

## auth.py

JWT verify.

Extract claims.

---

## rate_limit.py

Redis-backed.

Example:

```text id="t4q8m2"
100 req/min
```

---

## logging.py

Structured logs.

---

## cors.py

Frontend origin allowlist.

---

# 6. Service Discovery

Uses env:

```text id="q2n7r4"
AUTH_URL
POLICY_URL
FILE_URL
AUDIT_URL
RISK_URL
WORKER_URL
```

From root `.env`.

Never hardcode.

---

# 7. Standard Response Format

Normalize everything:

Success:

```json id="m5p1q8"
{
  "success": true,
  "data": {},
  "message": null
}
```

Error:

```json id="v8r3n6"
{
  "success": false,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Invalid credentials"
  }
}
```

Consistent API.

---

# 8. Aggregation Endpoints

Build:

## GET /api/dashboard

Collect:

* profile
* files count
* alerts
* risk
* recent activity

Single payload.

---

## GET /api/user-context

Returns:

```json id="n1m6q4"
{
  "user": {},
  "permissions": [],
  "risk_score": 31
}
```

Used globally.

---

# 9. Future

Later:

* websocket hub
* streaming uploads
* SSE alerts
* circuit breakers
* service health routing
* retries
* tracing

---

# 10. Implementation Order

1. health endpoint
2. auth proxy
3. JWT middleware
4. file proxy
5. policy proxy
6. aggregation routes
7. rate limiting
8. websockets

---

# 11. Rules

Gateway must:

* stay thin
* no DB access
* no business logic
* only routing + validation + aggregation
* service-to-service via internal URLs
