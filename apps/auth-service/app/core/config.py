import os


def required(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Missing env var: {key}")
    return value


class Settings:
    PROJECT_NAME = required("PROJECT_NAME")
    ENVIRONMENT = required("ENVIRONMENT")

    POSTGRES_HOST = required("POSTGRES_HOST")
    POSTGRES_PORT = int(required("POSTGRES_PORT"))
    POSTGRES_DB = required("POSTGRES_DB")
    POSTGRES_USER = required("POSTGRES_USER")
    POSTGRES_PASSWORD = required("POSTGRES_PASSWORD")

    REDIS_HOST = required("REDIS_HOST")
    REDIS_PORT = int(required("REDIS_PORT"))

    MINIO_HOST = required("MINIO_HOST")
    MINIO_PORT = int(required("MINIO_PORT"))
    MINIO_ROOT_USER = required("MINIO_ROOT_USER")
    MINIO_ROOT_PASSWORD = required("MINIO_ROOT_PASSWORD")
    MINIO_BUCKET = required("MINIO_BUCKET")

    AUTH_URL = required("AUTH_URL")
    POLICY_URL = required("POLICY_URL")
    FILE_URL = required("FILE_URL")
    AUDIT_URL = required("AUDIT_URL")
    RISK_URL = required("RISK_URL")
    WORKER_URL = required("WORKER_URL")

    JWT_SECRET = required("JWT_SECRET")
    JWT_ALGORITHM = required("JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES = os.getenv("JWT_EXPIRE_MINUTES", "15")

    # Auth policy — read from env with safe defaults
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    OTP_EXPIRY_SECONDS = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))
    TRUSTED_DEVICE_SCORE = int(os.getenv("TRUSTED_DEVICE_SCORE", "70"))


settings = Settings()
