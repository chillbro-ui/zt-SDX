import uuid

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    role = Column(String, nullable=False)
    department = Column(String)

    clearance_level = Column(Integer, default=1)
    device_trust = Column(Integer, default=0)
    risk_score = Column(Integer, default=0)

    mfa_enabled = Column(Boolean, default=True)
    status = Column(String, default="ACTIVE")