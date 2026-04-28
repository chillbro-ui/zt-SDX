# File Service Specification — ZT-SDX

## Purpose

File-service manages secure file lifecycle.

It owns:

* upload orchestration
* metadata persistence
* classification
* access control hook
* sharing
* revocation
* retention
* secure download
* versioning
* file state transitions

File-service does NOT directly do heavy processing.

Heavy work → worker-service.

ML classification/risk augmentation → risk-service.

File-service coordinates.

---

# 1. Ownership

Directory:

```text id="j4m8q2"
apps/file-service/
```

Structure:

```text id="q7p1n5"
app/
├── api/
├── models/
├── services/
├── core/
├── storage/
├── sharing/
├── lifecycle/
├── validators/
└── crypto/
```

---

# 2. Core Data Ownership

Primary DB tables:

```text id="n6q2m8"
files
shares
file_versions
file_access_logs
```

Main source:

PostgreSQL

Blob storage:

MinIO

Hot cache:

Redis

---

# 3. File Lifecycle

State machine:

```text id="u1m7q4"
UPLOADING
↓
QUEUED_SCAN
↓
SCANNING
↓
CLASSIFIED
↓
ENCRYPTED
↓
ACTIVE
↓
ARCHIVED
↓
DELETED
```

Error branch:

```text id="b8q1m6"
QUARANTINED
BLOCKED
FAILED
```

This state must be stored.

---

# 4. Upload Flow

Client:

```text id="r5m2q8"
POST /files/upload
```

Flow:

```text id="c2q7m1"
validate request
↓
hash stream (SHA256)
↓
store raw object in MinIO
↓
insert metadata row
↓
enqueue worker scan
↓
mark QUEUED_SCAN
↓
return upload_id
```

Return:

```json id="p7m1q5"
{
  "file_id": "uuid",
  "status": "QUEUED_SCAN"
}
```

---

# 5. Metadata Model

File record:

```json id="k4q8m2"
{
  "id": "uuid",
  "owner_id": "uuid",
  "filename": "report.pdf",
  "stored_name": "uuid_object_key",
  "mime_type": "application/pdf",
  "size": 123456,
  "sha256": "...",
  "classification": "CONFIDENTIAL",
  "status": "ACTIVE",
  "risk_score": 12,
  "version": 1,
  "created_at": "..."
}
```

---

# 6. Validation Layer

Implement:

```text id="m1q7r3"
app/validators/
```

Checks:

* extension allowlist
* MIME validation
* max size
* filename sanitation
* duplicate detection
* content sniffing
* malware scan result

Allowed types from root env:

```text id="t6m2q8"
ALLOWED_FILE_TYPES
MAX_UPLOAD_MB
```

---

# 7. Crypto Layer

Implement:

```text id="w3q8m1"
app/crypto/
```

Features:

* file key generation
* encryption at rest
* signed download URLs
* token hashing
* watermark signature
* optional per-user encryption key

Store encrypted blobs.

Never raw sensitive files.

---

# 8. Access Flow

Download:

```text id="x7m1q4"
GET /files/{id}
```

Flow:

```text id="q2m8r5"
fetch metadata
↓
call policy-service
↓
call risk-service
↓
decision
↓
generate signed MinIO URL
↓
audit log
↓
return stream/url
```

Possible outcomes:

```text id="n5q1m7"
ALLOW
DENY
MFA_REQUIRED
LIMITED_ACCESS
WATERMARK_ONLY
```

---

# 9. Sharing Engine

Implement:

```text id="g8m2q4"
app/sharing/
```

Create share:

Options:

* expiry
* max downloads
* device lock
* IP allowlist
* watermark
* OTP required
* one-time access

Record:

```json id="r1q7m3"
{
  "token_hash": "...",
  "expiry": "...",
  "downloads_left": 3
}
```

Never store raw token.

Store hash.

---

# 10. Versioning

Upload replacement:

```text id="u4m8q2"
v1
v2
v3
```

Track lineage.

Support rollback.

Version rows in:

```text id="b7q1m5"
file_versions
```

---

# 11. Search

Filters:

* owner
* type
* classification
* date
* status
* risk score

Use DB indexes.

Later semantic search possible.

---

# 12. APIs

Core:

```text id="p3m7q1"
POST   /files/upload
GET    /files
GET    /files/{id}
DELETE /files/{id}
PUT    /files/{id}
```

Sharing:

```text id="m6q2r4"
POST /shares
GET  /shares
PUT  /shares/{id}/revoke
```

Admin:

```text id="t1m8q6"
GET /files/quarantined
GET /files/high-risk
```

---

# 13. Worker Integration

Send jobs:

```text id="v5q1m3"
SCAN_FILE
CLASSIFY_FILE
EXTRACT_METADATA
ENCRYPT_FILE
DELETE_FILE
```

Consume result callbacks.

Update state.

---

# 14. Risk Integration

Ask risk-service:

Inputs:

* file sensitivity
* user profile
* access pattern

Receive:

```json id="k8m2q5"
{
  "risk_score": 41,
  "recommended_action": "MFA_REQUIRED"
}
```

Apply controls.

---

# 15. Audit Integration

Log:

* upload
* download
* share create
* revoke
* delete
* quarantine
* access denied

Every event.

---

# 16. Initial Build Order

1. ORM models
2. upload endpoint
3. MinIO storage wrapper
4. metadata CRUD
5. share CRUD
6. worker queue
7. signed downloads
8. policy integration
9. risk integration
10. encryption

---

# 17. Rules

File-service is source of truth for metadata.

Never:

* bypass policy
* bypass audit
* store raw secrets in DB
* expose raw MinIO keys
* skip hashing
