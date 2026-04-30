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


settings = Settings()
