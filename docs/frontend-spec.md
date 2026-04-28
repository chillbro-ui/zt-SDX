# Frontend Specification — ZT-SDX

## Purpose

Frontend is the user interaction layer for ZT-SDX.

Responsibilities:

* Authentication UI
* Dashboard
* File upload / management
* Sharing UI
* Audit viewer
* Alerts / risk visibility
* Policy admin
* Admin user management

Frontend does NOT implement security logic.

Frontend consumes APIs.

---

# 1. Ownership

Directory:

```text id="2l8r6m"
apps/frontend/
```

Recommended structure:

```text id="x7p4k2"
src/
├── pages/
├── components/
├── layouts/
├── hooks/
├── services/
├── store/
├── types/
├── utils/
├── assets/
└── router/
```

---

# 2. Stack

Recommended:

* React
* TypeScript
* TailwindCSS
* React Router
* Axios
* Zustand / Redux Toolkit
* React Query

---

# 3. Core Layout

App shell:

```text id="s1q7m3"
Top Navbar
Left Sidebar
Main Content
Right Notification Panel (optional)
```

Sidebar:

* Dashboard
* Files
* Upload
* Shared Links
* Alerts
* Audit
* Policies
* Users
* Settings

---

# 4. Screens

## A) Login

Route:

```text id="m6p2r8"
/login
```

Fields:

* email
* password
* device fingerprint hidden field

Flow:

Login → OTP challenge → Verify OTP → Dashboard

API:

```text id="h4k9n1"
POST /auth/login
POST /auth/verify-otp
```

---

## B) Dashboard

Route:

```text id="r8q3m5"
/dashboard
```

Widgets:

* user risk score
* recent files
* recent alerts
* shares active
* audit summary
* device trust
* storage usage

Charts:

* activity heatmap
* downloads trend
* alert severity distribution

---

## C) File Explorer

Route:

```text id="j2m7p4"
/files
```

Table:

Columns:

* filename
* owner
* size
* sensitivity
* status
* risk score
* created_at

Actions:

* view
* download
* share
* revoke
* delete

Filters:

* sensitivity
* owner
* status
* date

---

## D) Upload Center

Route:

```text id="c9q1n6"
/upload
```

Features:

* drag drop
* progress bar
* metadata form
* sensitivity selection
* preview
* upload status

After upload:

show:

* hash
* classification
* scan result
* risk score

---

## E) Share Center

Route:

```text id="v5r8m2"
/shares
```

Features:

Create share:

* recipient
* expiry
* download limit
* device lock
* watermark toggle

List shares:

* active
* expired
* revoked

Actions:

* revoke
* extend
* copy link

---

## F) Alerts Center

Route:

```text id="n1p6q4"
/alerts
```

Cards:

* type
* severity
* actor
* details
* timestamp

Filters:

* LOW
* MEDIUM
* HIGH
* CRITICAL

Realtime preferred.

---

## G) Audit Viewer

Route:

```text id="k7m3r1"
/audit
```

Table:

* actor
* action
* resource
* result
* IP
* timestamp

Search:

* user
* action
* file
* date

---

## H) Policy Admin

Route:

```text id="t4q9m6"
/policies
```

Features:

Create policy:

* role
* resource sensitivity
* device trusted toggle
* risk threshold
* action

Visual rule builder preferred.

---

## I) User Management

Route:

```text id="w8n2p5"
/users
```

Columns:

* name
* email
* role
* department
* clearance
* trust
* risk
* status

Actions:

* suspend
* revoke
* reset MFA
* edit role

---

# 5. API Integration

Frontend talks ONLY to:

```text id="y3m7q2"
gateway-api
```

Never directly:

```text id="q6p1n8"
auth-service
file-service
risk-service
```

Gateway abstracts internal services.

Base URL:

```text id="m9r4k7"
http://localhost:8000
```

Axios client:

```ts id="r2q8m1"
api.ts
```

single source.

---

# 6. Contracts

Types must mirror:

```text id="c5n7p3"
shared/contracts/
```

Examples:

* auth.json
* files.json
* shares.json
* alerts.json
* audit.json
* users.json
* policies.json

No custom shapes.

---

# 7. State

Global store:

* auth state
* token
* current user
* risk score
* notifications
* theme

Server cache:

* files
* alerts
* policies
* users

---

# 8. Realtime

Prefer websocket/SSE for:

* alerts
* audit events
* upload progress
* risk score updates

Fallback polling:

10–30 sec.

---

# 9. UI Theme

Security dashboard aesthetic:

* dark mode default
* muted graphite backgrounds
* accent:

  * cyan
  * amber
  * red severity states

Cards:

* glassmorphism optional
* dense information
* enterprise feel

---

# 10. Build Order

Implement:

1. app shell layout
2. login
3. dashboard
4. file explorer
5. upload
6. shares
7. alerts
8. audit
9. policy admin
10. users admin

---

# 11. Deliverables

Need:

* responsive UI
* reusable component system
* strict typing
* contract alignment
* clean routing
* API abstraction layer
* polished UX
