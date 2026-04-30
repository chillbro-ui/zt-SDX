import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
    )

    token_hash = Column(
        String,
    )

    ip = Column(
        String(64),
    )

    device_id = Column(
        UUID(as_uuid=True),
    )

    risk_score = Column(
        Integer,
    )

    expires_at = Column(
        DateTime,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
