import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name = Column(
        String(64),
        unique=True,
        nullable=False,
    )

    privilege_level = Column(
        Integer,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
