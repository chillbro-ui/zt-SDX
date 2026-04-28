import uuid

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.core.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    role = Column(
        String(64),
        nullable=False,
    )

    resource_sensitivity = Column(
        ARRAY(String),
        nullable=False,
    )

    device_trusted = Column(
        Boolean,
        default=False,
    )

    risk_score_lt = Column(
        Integer,
        nullable=False,
    )

    action = Column(
        String(32),
        nullable=False,
    )