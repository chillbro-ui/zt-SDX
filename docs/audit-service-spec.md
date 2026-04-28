# Audit Service Specification — ZT-SDX

## Purpose

Audit-service is the immutable event ledger of ZT-SDX.

It records:

* authentication events
* file access events
* sharing events
* policy decisions
* risk alerts
* admin actions
* system events

Primary goals:

* accountability
* forensic investigation
* tamper detection
* compliance logging
* historical analytics

Audit is append-only.

Never update old records.

Never delete records.

---

# 1. Ownership

Directory:

```text id="c7m2q5"
apps/audit-service/
```

Internal structure:

```text id="v1p8n4"
app/
├── api/
├── models/
├── services/
├── core/
├── chain/
├── export/
└── analytics/
```

---

# 2. Event Producers

Audit consumes events from all services.

---

## Auth Service

Events:

```text id="r5n1m7"
LOGIN_SUCCESS
LOGIN_FAILED
REGISTER
PASSWORD_RESET
OTP_SENT
OTP_FAILED
MFA_VERIFIED
SESSION_REVOKED
NEW_DEVICE_LOGIN
```

Example:

```json id="u8q3m1"
{
  "service": "auth",
  "event": "LOGIN_SUCCESS",
  "actor": "user_uuid",
  "ip": "1.2.3.4",
  "device_id": "abc123",
  "geo": "IN",
  "timestamp": "..."
}
```

---

## File Service

Events:

```text id="p2r7n4"
UPLOAD
DOWNLOAD
DELETE
SHARE_CREATED
SHARE_REVOKED
DOWNLOAD_LIMIT_HIT
FILE_CLASSIFIED
FILE_ENCRYPTED
```

---

## Policy Service

Events:

```text id="m6q1p8"
ALLOW
DENY
MFA_REQUIRED
ACCESS_ESCALATED
```

---

## Risk Service

Events:

```text id="k9m3q2"
RISK_HIGH
RISK_CRITICAL
ANOMALY_DETECTED
ALERT_CREATED
MODEL_RETRAINED
```

---

## Admin

Events:

```text id="w4p7n1"
ROLE_CHANGED
USER_SUSPENDED
POLICY_UPDATED
MFA_RESET
PERMISSION_REVOKED
```

---

# 3. Event Schema

Record:

```json id="b7n2q5"
{
  "id": "uuid",
  "service": "auth",
  "event": "LOGIN_SUCCESS",
  "actor": "uuid",
  "resource": "file/user/policy",
  "resource_id": "uuid",
  "ip": "1.2.3.4",
  "metadata": {},
  "result": "SUCCESS",
  "severity": "LOW",
  "prev_hash": "...",
  "hash": "...",
  "created_at": "..."
}
```

Stored in:

```text id="q1m8r4"
audit_logs
```

---

# 4. Hash Chain Integrity

Core feature.

Every log links to previous log.

Structure:

```text id="t5q2m7"
log1.hash
   ↓
log2.prev_hash = log1.hash
log2.hash = SHA256(log2 data + prev_hash)
   ↓
log3.prev_hash = log2.hash
```

Creates immutable chain.

Tampering breaks chain.

Implement in:

```text id="g8p3n1"
app/chain/
```

Functions:

```text id="j2m7q4"
compute_hash()
get_last_hash()
verify_chain()
```

---

# 5. Severity Engine

Levels:

```text id="n6q1m8"
INFO
LOW
MEDIUM
HIGH
CRITICAL
```

Examples:

LOW:

```text id="h9m4q2"
normal login
```

MEDIUM:

```text id="v3p8n5"
new device login
```

HIGH:

```text id="c7q2m1"
policy deny
rapid download
```

CRITICAL:

```text id="k4n7p3"
data exfiltration
admin abuse
repeated brute force
```

---

# 6. Storage

Primary:

PostgreSQL

Hot cache:

Redis

Exports:

MinIO

archive:

```text id="r8m1q6"
daily logs
weekly bundles
signed export snapshots
```

---

# 7. APIs

## POST /log

Append event.

Input:

producer payload.

---

## GET /events

Query logs.

Filters:

* service
* actor
* severity
* event
* date

---

## GET /events/{id}

Detailed event.

---

## GET /verify-chain

Verify integrity.

Return:

```json id="m5q8n2"
{
  "valid": true
}
```

---

## GET /analytics

Return:

* events/hour
* top users
* top alerts
* suspicious activity

---

## GET /export

CSV / JSON export.

---

# 8. Analytics

Build:

```text id="d1p7m4"
app/analytics/
```

Metrics:

* failed logins/day
* denied actions/day
* sensitive downloads/day
* anomaly count
* admin changes
* user activity map

---

# 9. Frontend Integration

Audit dashboard consumes:

```text id="x6m2q8"
/events
/analytics
/verify-chain
```

Features:

* timeline
* filters
* export
* integrity badge

---

# 10. Implementation Order

1. model
2. create log endpoint
3. hash chain
4. verify chain
5. query API
6. analytics
7. export pipeline

---

# 11. Rules

Audit-service:

* append-only
* no updates
* no deletes
* immutable hashes
* structured metadata
* every critical action logged
