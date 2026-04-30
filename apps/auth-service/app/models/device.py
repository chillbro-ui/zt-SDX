import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
    )

    fingerprint = Column(
        String,
    )

    trusted = Column(
        Boolean,
        default=False,
    )

    last_seen = Column(
        DateTime,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
