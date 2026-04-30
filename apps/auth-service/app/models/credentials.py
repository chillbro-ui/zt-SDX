import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class Credentials(Base):
    __tablename__ = "credentials"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
    )

    temp_password_hash = Column(
        String,
    )

    activated = Column(
        Boolean,
        default=False,
    )

    activation_code = Column(
        String,
    )

    password_changed = Column(
        Boolean,
        default=False,
    )

    mfa_enabled = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
