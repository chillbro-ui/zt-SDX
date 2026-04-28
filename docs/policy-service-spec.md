# Policy Service Specification — ZT-SDX

## Purpose

Policy-service is the authorization and access decision layer.

It evaluates:

* who is requesting
* what resource is being requested
* sensitivity of resource
* device trust
* current risk score
* contextual restrictions
* organization rules

Output:

```text id="p4m8q1"
ALLOW
DENY
MFA_REQUIRED
LIMITED_ACCESS
READ_ONLY
WATERMARK_ONLY
QUARANTINE
```

Policy does not authenticate users.

Auth handles identity.

Policy handles authorization.

---

# 1. Ownership

Directory:

```text id="k7q2m5"
apps/policy-service/
```

Structure:

```text id="u1m7q4"
app/
├── api/
├── models/
├── services/
├── core/
├── engine/
├── rules/
├── evaluators/
└── context/
```

---

# 2. Inputs

Policy consumes normalized context.

Input contract:

```json id="b8q1m6"
{
  "user": {
    "id": "uuid",
    "role": "ADMIN",
    "department": "Security",
    "clearance_level": 4,
    "device_trust": 81
  },
  "resource": {
    "type": "FILE",
    "id": "uuid",
    "classification": "CONFIDENTIAL",
    "owner_id": "uuid"
  },
  "action": "DOWNLOAD",
  "context": {
    "risk_score": 42,
    "geo": "IN",
    "ip": "1.2.3.4",
    "time": "2026-04-28T10:00:00Z"
  }
}
```

Output:

```json id="n5q1m7"
{
  "decision": "ALLOW",
  "reason": "ROLE_ALLOWED",
  "controls": [
    "AUDIT",
    "WATERMARK"
  ]
}
```

---

# 3. Data Ownership

Primary table:

```text id="g8m2q4"
policies
```

Secondary:

```text id="r1q7m3"
policy_history
policy_templates
exceptions
```

Primary storage:

PostgreSQL

Fast cache:

Redis

Redis stores compiled policies.

---

# 4. Decision Pipeline

Evaluation order:

```text id="u4m8q2"
identity
↓
role
↓
resource classification
↓
ownership
↓
department rule
↓
device trust
↓
risk score
↓
time/location constraints
↓
exception rules
↓
final decision
```

Short-circuit deny allowed.

---

# 5. Rule Model

Rule:

```json id="b7q1m5"
{
  "id": "uuid",
  "name": "Confidential download rule",
  "role": "EMPLOYEE",
  "resource_type": "FILE",
  "classification": "CONFIDENTIAL",
  "action": "DOWNLOAD",
  "min_clearance": 3,
  "min_device_trust": 60,
  "max_risk_score": 40,
  "decision": "ALLOW",
  "controls": ["AUDIT"]
}
```

---

# 6. Rule Engine

Implement:

```text id="p3m7q1"
app/engine/
```

Pipeline:

Load policy set:

```text id="m6q2r4"
DB → Redis cache
```

Compile rules.

Evaluate request.

Return decision.

Functions:

```text id="t1m8q6"
load_rules()
compile_rules()
evaluate()
explain_decision()
```

---

# 7. Evaluators

Implement:

```text id="v5q1m3"
app/evaluators/
```

Modules:

```text id="k8m2q5"
role_eval.py
classification_eval.py
ownership_eval.py
device_eval.py
risk_eval.py
geo_eval.py
time_eval.py
exception_eval.py
```

Each returns:

```text id="a1q7m4"
PASS
FAIL
ESCALATE
```

---

# 8. Risk Integration

Consumes from risk-service:

```json id="r4m8q2"
{
  "risk_score": 55,
  "signals": [
    "new_device",
    "burst_download"
  ],
  "recommended_action": "MFA_REQUIRED"
}
```

Policy may convert:

```text id="q2m7p5"
ALLOW → MFA_REQUIRED
ALLOW → LIMITED_ACCESS
ALLOW → DENY
```

Risk modifies authorization.

---

# 9. Device Trust

Device trust thresholds:

```text id="w6q1m8"
80+ trusted
60–79 moderate
30–59 low
0–29 untrusted
```

Rules may require trusted device.

Example:

```text id="x3m8q1"
secret files require >=70
```

---

# 10. Context Restrictions

Support:

* time window access
* IP allowlist
* geo allowlist
* VPN restrictions
* managed device only
* download count limits
* session age

---

# 11. Controls

Decision may include controls:

```text id="p7m2q4"
AUDIT
MFA
WATERMARK
DOWNLOAD_LIMIT
READ_ONLY
SESSION_SHORTEN
REQUIRE_APPROVAL
QUARANTINE
```

File-service applies controls.

---

# 12. APIs

Core:

```text id="n1m7q5"
POST /evaluate
```

Returns decision.

---

Admin:

```text id="g4q8m2"
POST /policies
GET /policies
PUT /policies/{id}
DELETE /policies/{id}
```

---

Explainability:

```text id="u8m1q3"
POST /explain
```

Return evaluation path.

Example:

```json id="r5q2m7"
{
  "checks": [
    "role passed",
    "classification passed",
    "risk escalated"
  ],
  "decision": "MFA_REQUIRED"
}
```

---

# 13. Audit Integration

Log:

* allow
* deny
* escalations
* overrides
* policy changes

Every decision.

---

# 14. Worker Integration

Async jobs:

```text id="c2m8q4"
POLICY_RECOMPILE
CACHE_REFRESH
POLICY_ANALYTICS
```

---

# 15. Initial Build Order

1. policy ORM
2. CRUD
3. simple rule evaluator
4. evaluate endpoint
5. Redis cache
6. explain endpoint
7. risk integration
8. control engine

---

# 16. Rules

Policy-service is authoritative.

Never bypass policy.

Every sensitive action:

```text id="m7q1p5"
Auth → Risk → Policy → Resource
```

Policy is the final gate.
