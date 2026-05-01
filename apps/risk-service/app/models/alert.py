from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.db import Base

class Alert(Base):
    __tablename__ = "risk_alerts"

    id = Column(String, primary_key=True, default=lambda: __import__('uuid').uuid4().hex)
    user_id = Column(String, index=True)
    alert_type = Column(String)
    severity = Column(String)
    score_delta = Column(Float)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())