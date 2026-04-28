# Worker Service Specification — ZT-SDX

## Purpose

Worker-service handles asynchronous and background processing.

It exists to keep core APIs fast.

Move expensive work here:

* file scanning
* metadata extraction
* encryption jobs
* thumbnail generation
* scheduled cleanup
* expired share revocation
* analytics aggregation
* audit export batching
* notification dispatch
* model retraining trigger

Worker = execution engine.

---

# 1. Ownership

Directory:

```text id="z4n7p2"
apps/worker-service/
```

Structure:

```text id="r1m8q4"
app/
├── jobs/
├── queues/
├── processors/
├── schedulers/
├── services/
├── api/
└── core/
```

---

# 2. Data Flow

```text id="n5q2m7"
Service produces job
      ↓
Redis queue
      ↓
Worker consumes
      ↓
Process task
      ↓
Store result
      ↓
Notify source service
      ↓
Audit log
```

---

# 3. Job Producers

---

## File Service → Worker

Produces:

```text id="p8m1q6"
SCAN_FILE
CLASSIFY_FILE
EXTRACT_METADATA
GENERATE_THUMBNAIL
ENCRYPT_FILE
DELETE_FILE
```

Example payload:

```json id="m3q7n1"
{
  "job_type": "SCAN_FILE",
  "file_id": "uuid",
  "bucket": "zt-files",
  "object_key": "abc.pdf"
}
```

---

## Auth Service → Worker

Produces:

```text id="c6m2q8"
SEND_OTP
SEND_LOGIN_ALERT
SEND_SECURITY_WARNING
SESSION_CLEANUP
```

Example:

```json id="v1q8m4"
{
  "job_type": "SEND_OTP",
  "user_id": "uuid",
  "email": "x@y.com"
}
```

---

## Policy Service → Worker

Produces:

```text id="k7m3p1"
REVOKE_ACCESS_CACHE
POLICY_RECOMPUTE
```

---

## Risk Service → Worker

Produces:

```text id="w2q7n5"
MODEL_RETRAIN
FEATURE_AGGREGATION
ALERT_NOTIFICATION
```

---

## Audit Service → Worker

Produces:

```text id="g9m1q3"
EXPORT_LOGS
ARCHIVE_LOGS
VERIFY_CHAIN_BATCH
```

---

# 4. Queue Layer

Use Redis.

Implement:

```text id="y4p8m2"
app/queues/
```

Queues:

```text id="q1m7r4"
file_jobs
auth_jobs
policy_jobs
risk_jobs
audit_jobs
system_jobs
```

Priority queues:

```text id="t6q2m8"
critical
high
normal
low
```

Examples:

critical:

```text id="d3m8q1"
security alert
session revoke
```

low:

```text id="x8q1m5"
thumbnail generation
analytics batch
```

---

# 5. Processors

Implement:

```text id="p5m2q7"
app/processors/
```

Modules:

```text id="m1q8r3"
file_processor.py
auth_processor.py
policy_processor.py
risk_processor.py
audit_processor.py
system_processor.py
```

Dispatcher:

```python id="f7m3q1"
job_type -> processor
```

Example:

```text id="n2q7m4"
SCAN_FILE -> file_processor
SEND_OTP -> auth_processor
EXPORT_LOGS -> audit_processor
```

---

# 6. File Pipeline

File workflow:

```text id="v6m1q8"
upload
 ↓
store raw object
 ↓
queue SCAN_FILE
 ↓
virus scan
 ↓
metadata extraction
 ↓
classification
 ↓
encrypt
 ↓
mark ACTIVE
 ↓
audit event
```

Store results in:

PostgreSQL

Objects in:

MinIO

---

# 7. Scheduler

Implement:

```text id="r4q8m1"
app/schedulers/
```

Periodic jobs:

Every 5 min:

```text id="j7m2q5"
expire shares
cleanup sessions
```

Every hour:

```text id="b1q6m8"
aggregate analytics
```

Daily:

```text id="u5m3q2"
archive audit logs
verify hash chain
recompute trust
cleanup orphan files
```

Weekly:

```text id="k8q1m4"
risk retraining trigger
```

---

# 8. APIs

Minimal control API.

## GET /health

status.

---

## GET /queues

queue depth.

Example:

```json id="q3m7n1"
{
  "file_jobs": 18,
  "auth_jobs": 2
}
```

---

## POST /enqueue

manual enqueue.

---

## GET /jobs/{id}

status:

```text id="m6q2r8"
queued
running
success
failed
retrying
```

---

## POST /retry/{id}

manual retry.

---

# 9. Retry Strategy

Failures:

```text id="t1m8q4"
1st retry → 10 sec
2nd retry → 1 min
3rd retry → 5 min
dead-letter queue
```

Store failed payloads.

Never silently drop jobs.

---

# 10. Observability

Track:

* queue size
* avg processing time
* failures
* retries
* throughput

Metrics dashboard later.

---

# 11. Initial Build Order

1. Redis queue wrapper
2. enqueue API
3. dispatcher
4. processors
5. scheduler
6. retries
7. monitoring

---

# 12. Rules

Worker must:

* be idempotent
* retry safely
* log failures
* never block request path
* process jobs independently
* scale horizontally later
