import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class Share(Base):
    __tablename__ = "shares"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    file_id = Column(
        UUID(as_uuid=True),
        nullable=False,
    )

    token_hash = Column(
        String,
        nullable=False,
    )

    recipient = Column(
        String(255),
    )

    expiry = Column(
        DateTime,
    )

    downloads_left = Column(
        Integer,
        default=1,
    )

    device_lock = Column(
        Boolean,
        default=False,
    )

    watermark = Column(
        Boolean,
        default=True,
    )

    status = Column(
        String(32),
        default="ACTIVE",
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
