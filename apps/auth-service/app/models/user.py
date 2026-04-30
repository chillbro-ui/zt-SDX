import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Flat role/department strings — used for quick access without joins
    # role_id / department_id are the FK references to the normalized tables
    role = Column(String(64))
    department = Column(String(128))

    # Enterprise hierarchy FKs
    org_id = Column(UUID(as_uuid=True))
    department_id = Column(UUID(as_uuid=True))
    role_id = Column(UUID(as_uuid=True))
    employee_code = Column(String, unique=True)
    manager_id = Column(UUID(as_uuid=True))

    clearance_level = Column(Integer, default=1)
    device_trust = Column(Integer, default=0)
    risk_score = Column(Integer, default=0)

    mfa_enabled = Column(Boolean, default=True)
    status = Column(String, default="ACTIVE")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
