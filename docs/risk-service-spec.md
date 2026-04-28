# Risk Service Specification (ML / Security Analytics)

## Purpose

Risk-service is the system intelligence layer.

It computes:

* user risk score
* file access risk
* anomaly detection
* recommended security action

Output is consumed by:

* auth-service
* policy-service
* file-service
* audit-service

---

# 1. Service Ownership

Directory:

```text
apps/risk-service/
```

Internal structure:

```text
app/
├── api/
├── models/
├── services/
├── core/
├── scoring/
├── anomaly/
├── features/
└── training/
```

---

# 2. Inputs

Risk-service does NOT directly own user/file data.

It consumes telemetry.

---

## A) Auth Events

Source:

```text
auth-service
```

Examples:

```json
{
  "event": "LOGIN_SUCCESS",
  "user_id": "uuid",
  "device_id": "abc",
  "ip": "1.2.3.4",
  "geo": "IN",
  "timestamp": "..."
}
```

Also:

```json
{
  "event": "LOGIN_FAILED"
}
```

```json
{
  "event": "OTP_FAILED"
}
```

```json
{
  "event": "NEW_DEVICE_LOGIN"
}
```

Features extracted:

* failed login count
* new device
* geo mismatch
* time-of-day anomaly
* impossible travel

---

## B) File Events

Source:

```text
file-service
```

Examples:

```json
{
  "event": "FILE_UPLOAD",
  "user_id": "...",
  "file_type": "pdf",
  "size": 5000000,
  "sensitivity": "SECRET"
}
```

```json
{
  "event": "FILE_DOWNLOAD"
}
```

```json
{
  "event": "SHARE_CREATED"
}
```

Features:

* rapid download burst
* unusual file type
* large export
* high sensitivity access
* external share spike

---

## C) Policy Violations

Source:

```text
policy-service
```

Examples:

```json
{
  "event": "POLICY_DENY"
}
```

```json
{
  "event": "MFA_ESCALATED"
}
```

Features:

* repeated deny attempts
* privilege abuse
* abnormal access pattern

---

## D) Device Signals

Source:

```text
auth-service
```

Signals:

* new browser fingerprint
* VM / emulator
* TOR / VPN
* rooted device
* low trust device

---

# 3. Feature Store

He should build:

```text
app/features/
```

Feature vectors:

```python
{
  failed_logins_1h: 3,
  failed_logins_24h: 8,
  new_device: 1,
  geo_distance_km: 2500,
  rapid_download_count: 14,
  secret_file_accesses: 5,
  denied_attempts: 2,
  device_trust: 41
}
```

These become ML inputs.

Store in:

* Redis (hot)
* PostgreSQL (history)

---

# 4. Core Engine

Implement:

```text
app/scoring/
```

### Stage 1: rule engine

Immediate baseline:

Example:

```python
new_device → +20
vpn → +10
5 failed logins → +25
rapid download → +35
policy deny → +15
```

Produces score:

0–100

Levels:

```text
0-20   LOW
21-45  MEDIUM
46-70  HIGH
71+    CRITICAL
```

---

### Stage 2: ML model

Can add:

* Isolation Forest
* XGBoost
* RandomForest
* Autoencoder anomaly detection

Input:

feature vector

Output:

anomaly probability

Combine:

```text
final_score =
rule_score * 0.6 +
ml_score * 0.4
```

---

# 5. Alert Engine

Build:

```text
app/anomaly/
```

Generate:

```json
{
  "type": "RAPID_DOWNLOAD",
  "severity": "HIGH",
  "score_delta": 35
}
```

Other alerts:

* impossible travel
* brute force login
* suspicious sharing
* high sensitivity exfiltration
* privilege escalation

---

# 6. Database Tables

He owns:

```text
risk_profiles
risk_events
risk_features
alerts
```

---

# 7. API

Endpoints:

## POST /score

Input:

telemetry event

Output:

```json
{
  "risk_score": 47,
  "level": "HIGH",
  "recommended_action": "MFA_REQUIRED"
}
```

---

## GET /user/{id}/risk

returns:

current profile

---

## GET /alerts

returns:

recent alerts

---

## POST /train

manual retrain endpoint

---

# 8. Output Consumers

Auth:

```text
risk high → MFA
risk critical → deny
```

Policy:

```text
risk modifies allow/deny
```

File:

```text
high risk → watermark / restrict share
```

Audit:

```text
store alerts
```

---

# 9. Initial Implementation Order

1. feature extraction
2. rule engine
3. scoring API
4. alerts
5. Redis feature cache
6. ML model
7. retraining pipeline
