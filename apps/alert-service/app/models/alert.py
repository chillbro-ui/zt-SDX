import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String)
    severity = Column(String)
    actor = Column(UUID(as_uuid=True))
    score_delta = Column(Integer)
    details = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
