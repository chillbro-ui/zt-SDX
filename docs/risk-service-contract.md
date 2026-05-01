# ZT-SDX — Risk Service Contract

**Base URL (internal):** `http://risk-service:8000`  
**Owned by:** Analytics team (not the backend team)  
**Status:** Stub implementation — replace internals, keep the interface identical.

---

## Overview

The risk service scores a user/file combination and returns a risk level.  
It is called by:

- **Gateway API** — before every upload and download (policy gate)
- **Worker Service** — after every file upload (async DLP scan result)

Both callers fail open if this service is unavailable — they default to `risk_score: 10`.

---

## Endpoints

---

### POST `/risk/score`

Score a file + owner combination and return a risk level.

**Called by:** Gateway API, Worker Service

**Request (query params):**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `file_id` | string | ✅ | UUID of the file being scored |
| `owner_id` | string | ✅ | UUID of the user who owns/is accessing the file |

**Example request:**

```
POST /risk/score?file_id=uuid&owner_id=uuid
```

**Response `200` (JSON):**

```json
{
  "file_id": "uuid",
  "risk_score": 42,
  "label": "LOW",
  "status": "ACTIVE"
}
```

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | Echo of the input `file_id` |
| `risk_score` | integer | Score from `0` to `100` |
| `label` | string | `"LOW"` if score < 80, `"HIGH"` if score ≥ 80 |
| `status` | string | `"ACTIVE"` if score < 80, `"QUARANTINED"` if score ≥ 80 |

---

## Risk Score Thresholds

These thresholds are used by the **Gateway API** and **Policy Service** to make decisions:

| Score Range | Decision | Action |
|-------------|----------|--------|
| `0 – 29` | `ALLOW` | Proceed normally |
| `30 – 59` | `MFA_REQUIRED` | Step-up authentication required |
| `60 – 84` | `DENY` | Block + alert |
| `85 – 100` | `TERMINATE` | Revoke all sessions + lock account |

These thresholds are configured in `.env`:

```env
RISK_MFA_THRESHOLD=30
RISK_DENY_THRESHOLD=60
RISK_LOCK_THRESHOLD=85
```

---

## Risk Score Signals (for Analytics team to implement)

The stub currently returns a random score. The real implementation should compute score from these signals:

| Signal | Score Delta | Trigger | Implemented |
|--------|-------------|---------|-------------|
| New / unrecognised device | +25 | Device fingerprint not in DB | ✅ Auth-service (login) |
| Failed login attempts | +15 per attempt | Wrong password | ✅ Auth-service (login) |
| No device fingerprint | +10 | No fingerprint sent | ✅ Auth-service (login) |
| Login at unusual hour | +20 | Outside 06:00–22:00 UTC for this user | ❌ ML team |
| New geographic location | +30 | IP geolocation differs from usual | ❌ ML team |
| Rapid bulk downloads | +40 | > 10 downloads in 2 minutes | ❌ ML team |
| Multiple failed MFA attempts | +15 per attempt | Failed OTP verification | ❌ ML team |
| Shared link forwarded to new device | +35 | Device fingerprint mismatch on share | ❌ ML team |
| DLP quarantine triggered | +50 | DLP scanner flagged the file | ❌ ML team |
| Normal behaviour (time decay) | -5 per hour | Score decays toward baseline | ❌ ML team |

### Login Risk Score (already computed in auth-service)

The auth-service computes a **session-level risk score** at login time from signals it already has:

```python
login_risk = 0
login_risk += min(failed_attempts * 15, 45)  # failed attempts signal
login_risk += 25  # if device_fingerprint sent but device not trusted
login_risk += 10  # if no device fingerprint sent at all

# Thresholds (from .env):
# RISK_MFA_THRESHOLD=30  → trigger OTP challenge
# RISK_DENY_THRESHOLD=60 → block login entirely
```

This score is stored in the `sessions` table and included in the JWT payload as `risk_score`.

The **file-level risk score** (from `POST /risk/score`) is separate — it scores the file content and owner behavior, stored in `files.risk_score`, used by the policy engine for download decisions.

---

## How Callers Use the Response

### Gateway API (`apps/gateway-api/app/clients/risk_client.py`)

```python
risk_result = await risk_client.score(file_id=file_id, owner_id=user["id"])
risk_score = risk_result.get("risk_score", 10)  # defaults to 10 if service is down
```

The `risk_score` is then passed to the policy service:

```python
decision = await policy_client.evaluate(
    role=user["role"],
    resource="FILE",
    action="UPLOAD",
    clearance_level=1,
    risk_score=risk_score,
)
```

### Worker Service (`apps/worker-service/app/clients/risk_client.py`)

```python
result = risk_client.score(file_id=file_id, owner_id=owner_id)
score = result.get("risk_score", 0)
status = result.get("status", "ACTIVE")
```

The worker then calls `file_client.update_risk()` to update the file record with the score and status.

---

## Failure Behaviour

Both callers wrap the risk service call in a try/except:

```python
try:
    response = requests.post(f"{RISK_URL}/risk/score", params=..., timeout=2)
    return response.json()
except Exception:
    return {"risk_score": 10, "label": "LOW", "status": "ACTIVE"}
```

**If the risk service is down:**
- Gateway defaults to `risk_score=10` → policy likely allows the action
- Worker defaults to `risk_score=0` → file stays `ACTIVE`, no alert fired

This is intentional fail-open behaviour for uploads. The analytics team can change this to fail-closed by adjusting the default score.

---

## Current Stub Implementation

Location: `apps/risk-service/app/api/risk_routes.py`

```python
@router.post("/score")
def score(file_id: str, owner_id: str):
    risk = random.randint(0, 100)
    label = "HIGH" if risk >= 80 else "LOW"
    status = "QUARANTINED" if risk >= 80 else "ACTIVE"
    return {
        "file_id": file_id,
        "risk_score": risk,
        "label": label,
        "status": status,
    }
```

**To replace:** Swap the `random.randint` logic with real signal computation.  
**Do not change:** The endpoint path, query param names, or response field names.  
Changing any of those will break the gateway and worker without any code changes on our side.

---

## Future Endpoints (not yet implemented — analytics team to add)

These are referenced in the architecture document and will be needed later:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/risk/scores/{user_id}` | GET | Fetch current risk state for a user |
| `/risk/override` | POST | Security Officer manual override |
| `/risk/signals` | POST | Ingest a new signal event |

When these are added, the gateway team will wire them in.
