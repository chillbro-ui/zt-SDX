import uuid

from sqlalchemy import BigInteger, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class File(Base):
    __tablename__ = "files"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id = Column(
        UUID(as_uuid=True),
        nullable=False,
    )

    filename = Column(
        String,
        nullable=False,
    )

    stored_name = Column(
        String,
        nullable=False,
    )

    mime_type = Column(
        String(128),
    )

    size = Column(
        BigInteger,
    )

    sha256 = Column(
        String,
        nullable=False,
    )

    sensitivity = Column(
        String(32),
        default="INTERNAL",
    )

    status = Column(
        String(32),
        default="ACTIVE",
    )

    risk_score = Column(
        Integer,
        default=0,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )