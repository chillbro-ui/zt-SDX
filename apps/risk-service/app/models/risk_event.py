from sqlalchemy import Column, String, Float, JSON, DateTime
from sqlalchemy.sql import func
from app.core.db import Base

class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(String, primary_key=True, index=True, default=lambda: __import__('uuid').uuid4().hex)
    user_id = Column(String, index=True)
    event_type = Column(String)
    payload = Column(JSON)
    rule_score = Column(Float)
    ml_score = Column(Float)
    final_score = Column(Float)
    ip = Column(String, nullable=True)
    geo = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())