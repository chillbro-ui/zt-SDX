import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    domain = Column(String(255), unique=True)
    industry = Column(String(128))
    country = Column(String(128))
    size = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
