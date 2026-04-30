-- ============================================
-- ZT-SDX Database Schema
-- ============================================

-- ─── Core Application Tables ─────────────────

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(64),
    department VARCHAR(128),
    org_id UUID,
    department_id UUID,
    role_id UUID,
    employee_code VARCHAR(64) UNIQUE,
    manager_id UUID,
    clearance_level INT DEFAULT 1,
    device_trust INT DEFAULT 0,
    risk_score INT DEFAULT 0,
    mfa_enabled BOOLEAN DEFAULT TRUE,
    status VARCHAR(32) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    domain VARCHAR(255) UNIQUE,
    industry VARCHAR(128),
    country VARCHAR(128),
    size INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) UNIQUE NOT NULL,
    privilege_level INT NOT NULL
);

-- Seed roles
INSERT INTO roles (name, privilege_level) VALUES
    ('SUPER_ADMIN', 100),
    ('SECURITY_ADMIN', 90),
    ('DEPT_HEAD', 75),
    ('MANAGER', 60),
    ('EMPLOYEE', 20),
    ('AUDITOR', 50)
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    temp_password_hash TEXT,
    activated BOOLEAN DEFAULT FALSE,
    activation_code TEXT,
    password_changed BOOLEAN DEFAULT FALSE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    fingerprint TEXT,
    trusted BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT,
    ip VARCHAR(64),
    device_id UUID REFERENCES devices(id),
    risk_score INT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role_id UUID REFERENCES roles(id),
    activation_code TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── File Service Tables ──────────────────────

CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(id),
    filename VARCHAR NOT NULL,
    stored_name VARCHAR NOT NULL,
    mime_type VARCHAR(128),
    size BIGINT,
    sha256 VARCHAR NOT NULL,
    sensitivity VARCHAR(32) DEFAULT 'INTERNAL',
    status VARCHAR(32) DEFAULT 'QUARANTINED',
    risk_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    token_hash VARCHAR NOT NULL,
    recipient VARCHAR(255),
    expiry TIMESTAMP,
    downloads_left INT DEFAULT 1,
    device_lock BOOLEAN DEFAULT FALSE,
    watermark BOOLEAN DEFAULT TRUE,
    status VARCHAR(32) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Policy Service Tables ────────────────────

CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(64) NOT NULL,
    resource_sensitivity TEXT[] NOT NULL,
    device_trusted BOOLEAN DEFAULT FALSE,
    risk_score_lt INT NOT NULL,
    action VARCHAR(32) NOT NULL
);

-- ─── Audit Service Tables ─────────────────────

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- actor is String to accept both UUIDs and system labels like "gateway", "worker", "anonymous"
    actor VARCHAR,
    action VARCHAR(128),
    resource VARCHAR,
    ip VARCHAR(64),
    result VARCHAR(32),
    prev_hash VARCHAR,
    hash VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Alert Service Tables ─────────────────────

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR,
    severity VARCHAR,
    actor UUID,
    score_delta INT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Indexes ──────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS idx_users_department_id ON users(department_id);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_users_employee_code ON users(employee_code);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_departments_org_id ON departments(org_id);
CREATE INDEX IF NOT EXISTS idx_credentials_user_id ON credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_credentials_activation_code ON credentials(activation_code);
CREATE INDEX IF NOT EXISTS idx_devices_user_id ON devices(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_invitations_org_id ON invitations(org_id);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(email);
CREATE INDEX IF NOT EXISTS idx_invitations_activation_code ON invitations(activation_code);
CREATE INDEX IF NOT EXISTS idx_files_owner_id ON files(owner_id);
CREATE INDEX IF NOT EXISTS idx_files_status ON files(status);
CREATE INDEX IF NOT EXISTS idx_shares_token_hash ON shares(token_hash);
CREATE INDEX IF NOT EXISTS idx_shares_file_id ON shares(file_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- ─── Views ────────────────────────────────────

CREATE OR REPLACE VIEW v_user_hierarchy AS
SELECT
    u.id AS user_id,
    u.email,
    u.role,
    u.department,
    u.employee_code,
    u.status,
    u.clearance_level,
    u.device_trust,
    u.risk_score,
    o.name AS org_name,
    o.domain AS org_domain,
    d.name AS department_name,
    r.name AS role_name,
    r.privilege_level,
    m.email AS manager_email
FROM users u
LEFT JOIN organizations o ON u.org_id = o.id
LEFT JOIN departments d ON u.department_id = d.id
LEFT JOIN roles r ON u.role_id = r.id
LEFT JOIN users m ON u.manager_id = m.id;

CREATE OR REPLACE VIEW v_active_sessions AS
SELECT
    s.id AS session_id,
    s.ip,
    s.risk_score,
    s.expires_at,
    s.created_at AS session_created_at,
    u.id AS user_id,
    u.email,
    u.role,
    u.org_id
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.expires_at > NOW();
