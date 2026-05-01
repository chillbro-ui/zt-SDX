import os


def required(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Missing required env var: {key}")
    return value


class Settings:
    PROJECT_NAME = required("PROJECT_NAME")
    ENVIRONMENT = required("ENVIRONMENT")

    # ── Database ──────────────────────────────────────────────────────────────
    POSTGRES_HOST = required("POSTGRES_HOST")
    POSTGRES_PORT = int(required("POSTGRES_PORT"))
    POSTGRES_DB = required("POSTGRES_DB")
    POSTGRES_USER = required("POSTGRES_USER")
    POSTGRES_PASSWORD = required("POSTGRES_PASSWORD")

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_HOST = required("REDIS_HOST")
    REDIS_PORT = int(required("REDIS_PORT"))

    # ── MinIO (for ML model storage) ──────────────────────────────────────────
    MINIO_HOST = required("MINIO_HOST")
    MINIO_PORT = int(required("MINIO_PORT"))
    MINIO_ROOT_USER = required("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = required("MINIO_ROOT_PASSWORD")
    MINIO_BUCKET = required("MINIO_BUCKET")

    # ── JWT (for validating inbound tokens from other services) ───────────────
    JWT_SECRET = required("JWT_SECRET")
    JWT_ALGORITHM = required("JWT_ALGORITHM")

    # ── Inter-service URLs ────────────────────────────────────────────────────
    AUDIT_URL = required("AUDIT_URL")
    ALERT_URL = os.getenv("ALERT_URL", "http://alert-service:8000")

    # ── Scoring weights (tunable without code changes) ────────────────────────
    RULE_WEIGHT: float = float(os.getenv("RULE_WEIGHT", "0.6"))
    ML_WEIGHT: float = float(os.getenv("ML_WEIGHT", "0.4"))

    # ── Risk thresholds ───────────────────────────────────────────────────────
    RISK_MFA_THRESHOLD: int = int(os.getenv("RISK_MFA_THRESHOLD", "30"))
    RISK_DENY_THRESHOLD: int = int(os.getenv("RISK_DENY_THRESHOLD", "60"))
    RISK_LOCK_THRESHOLD: int = int(os.getenv("RISK_LOCK_THRESHOLD", "85"))


settings = Settings()
