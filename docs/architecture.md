# ZT-SDX Architecture & Development Guide

## 1. System Overview

ZT-SDX is a distributed, containerized, service-oriented system designed around security-first principles:

* Zero Trust Access
* Secure File Handling
* Risk-based Decision Engine
* Audit & Observability

The system runs entirely via Docker Compose and is composed of multiple backend services, shared infrastructure, and a frontend client.

---

## 2. High-Level Architecture

```
Frontend
   ↓
Gateway API
   ↓
---------------------------------
| Auth Service                  |
| Policy Service               |
| File Service                 |
| Risk Service                 |
| Audit Service                |
| Worker Service              |
---------------------------------
        ↓
Shared Infrastructure:
PostgreSQL | Redis | MinIO
```

---

## 3. Services and Responsibilities

### Gateway API

* Entry point for frontend
* Routes requests to internal services
* No business logic

### Auth Service

* User authentication
* JWT issuance
* OTP / MFA handling

### Policy Service

* Access control decisions
* Role + risk + sensitivity enforcement

### File Service

* File metadata management (DB)
* File storage (MinIO)
* Share token generation

### Risk Service

* Risk scoring engine
* Behavior analysis
* Alert triggering

### Audit Service

* Immutable event logging
* Hash chain for integrity

### Worker Service

* Background processing
* File scanning (DLP)
* Async jobs

---

## 4. Infrastructure

### PostgreSQL

* Stores:

  * users
  * files
  * shares
  * alerts
  * policies
  * audit_logs

### Redis

* Caching
* OTP storage
* Queue / temporary state

### MinIO

* Object storage for files

---

## 5. Project Structure

```
zt-SDX/
│
├── apps/
│   ├── frontend/
│   ├── gateway-api/
│   ├── auth-service/
│   ├── policy-service/
│   ├── file-service/
│   ├── audit-service/
│   ├── risk-service/
│   └── worker-service/
│
├── shared/
│   ├── contracts/   ← API payload definitions
│   ├── schemas/     ← DB models (source of truth)
│   └── sdk/         ← future client generation
│
├── infra/
│   ├── compose/
│   ├── postgres/
│   ├── redis/
│   ├── minio/
│   └── monitoring/
```

---

## 6. Contracts vs Schemas

### Contracts (`shared/contracts/`)

* Define API request/response shapes
* Used by frontend + backend
* Example:

  * auth.json
  * files.json

### Schemas (`shared/schemas/`)

* Define database structure
* Used by backend only
* Drives SQL + ORM models

---

## 7. Environment Configuration

### Root `.env`

Single source of truth for:

* DB credentials
* Redis config
* MinIO config
* Service URLs
* Security parameters

### Compose

All services load config via:

```
env_file: ../../.env
```

No hardcoding allowed.

---

## 8. Internal Service Communication

Docker network provides DNS:

```
auth-service:8000
file-service:8000
postgres:5432
redis:6379
minio:9000
```

Example:

```
POSTGRES_HOST=postgres
AUTH_URL=http://auth-service:8000
```

---

## 9. Backend Structure (per service)

```
app/
├── api/        ← route handlers
├── models/     ← ORM models
├── services/   ← business logic + CRUD
├── core/
│   ├── config.py
│   ├── db.py
│   ├── cache.py
│   └── storage.py (if needed)
```

---

## 10. Development Workflow

### Step 1: Start system

```
docker compose -f infra/compose/docker-compose.yml up --build -d
```

---

### Step 2: Pick service

Work only inside your assigned service.

Do NOT modify:

* infra/
* shared/contracts/
* shared/schemas/

without discussion.

---

### Step 3: Implement flow

1. Define ORM model (models/)
2. Implement CRUD (services/)
3. Expose API (api/)
4. Match contract (shared/contracts/)

---

### Step 4: Test

Use:

```
http://localhost:<port>/docs
```

---

## 11. Ports

| Service       | Port |
| ------------- | ---- |
| Gateway       | 8000 |
| Auth          | 8001 |
| Policy        | 8002 |
| File          | 8003 |
| Audit         | 8004 |
| Risk          | 8005 |
| Frontend      | 5173 |
| PostgreSQL    | 5432 |
| Redis         | 6379 |
| MinIO API     | 9000 |
| MinIO Console | 9001 |

---

## 12. Rules

* Do not hardcode values → use config
* Follow contracts strictly
* Keep service boundaries clean
* No cross-service DB access
* All communication via APIs

---

## 13. Current State

* Infrastructure fully wired
* Services running
* Contracts defined
* DB schema created
* No business logic implemented yet

---

## 14. Next Steps

1. ORM models
2. CRUD layer
3. Seed data
4. API endpoints
5. Frontend integration
6. Security logic

---

This document defines the system baseline. All development should align with it.
