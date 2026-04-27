CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(64) NOT NULL,
    department VARCHAR(128),
    clearance_level INT DEFAULT 1,
    device_trust INT DEFAULT 0,
    risk_score INT DEFAULT 0,
    mfa_enabled BOOLEAN DEFAULT TRUE,
    status VARCHAR(32) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY,
    owner_id UUID REFERENCES users(id),
    filename TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    mime_type VARCHAR(128),
    size BIGINT,
    sha256 TEXT NOT NULL,
    sensitivity VARCHAR(32),
    status VARCHAR(32),
    risk_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shares (
    id UUID PRIMARY KEY,
    file_id UUID REFERENCES files(id),
    token_hash TEXT NOT NULL,
    recipient VARCHAR(255),
    expiry TIMESTAMP,
    downloads_left INT DEFAULT 1,
    device_lock BOOLEAN DEFAULT TRUE,
    watermark BOOLEAN DEFAULT TRUE,
    status VARCHAR(32) DEFAULT 'ACTIVE'
);

CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY,
    type VARCHAR(128),
    severity VARCHAR(32),
    actor UUID REFERENCES users(id),
    score_delta INT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY,
    role VARCHAR(64),
    resource_sensitivity TEXT[],
    device_trusted BOOLEAN,
    risk_score_lt INT,
    action VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    actor UUID REFERENCES users(id),
    action VARCHAR(128),
    resource TEXT,
    ip VARCHAR(64),
    result VARCHAR(32),
    prev_hash TEXT,
    hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);