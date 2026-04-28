import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    actor = Column(
        UUID(as_uuid=True),
    )

    action = Column(
        String(128),
    )

    resource = Column(
        String,
    )

    ip = Column(
        String(64),
    )

    result = Column(
        String(32),
    )

    prev_hash = Column(
        String,
    )

    hash = Column(
        String,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )