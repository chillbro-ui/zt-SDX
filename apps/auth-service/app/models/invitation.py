import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class Invitation(Base):
    __tablename__ = "invitations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    org_id = Column(
        UUID(as_uuid=True),
    )

    email = Column(
        String(255),
        nullable=False,
    )

    role_id = Column(
        UUID(as_uuid=True),
    )

    activation_code = Column(
        String,
        nullable=False,
    )

    expires_at = Column(
        DateTime,
        nullable=False,
    )

    used = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )
