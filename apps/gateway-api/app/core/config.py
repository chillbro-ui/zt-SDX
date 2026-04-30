import os


def required(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise RuntimeError(f"Missing env var: {key}")
    return value


class Settings:
    PROJECT_NAME = required("PROJECT_NAME")
    ENVIRONMENT = required("ENVIRONMENT")

    REDIS_HOST = required("REDIS_HOST")
    REDIS_PORT = int(required("REDIS_PORT"))

    AUTH_URL = required("AUTH_URL")
    POLICY_URL = required("POLICY_URL")
    FILE_URL = required("FILE_URL")
    AUDIT_URL = required("AUDIT_URL")
    RISK_URL = required("RISK_URL")
    ALERT_URL = os.getenv("ALERT_URL", "http://alert-service:8000")
    WORKER_URL = required("WORKER_URL")


settings = Settings()
