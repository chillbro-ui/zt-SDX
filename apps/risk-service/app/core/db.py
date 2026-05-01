from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.base import Base  # noqa: F401 — re-exported so models can import from here
from app.core.config import settings


DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:"
    f"{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/"
    f"{settings.POSTGRES_DB}"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # reconnect on stale connections
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
