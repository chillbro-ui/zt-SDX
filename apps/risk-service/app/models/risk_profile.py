from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.sql import func
from app.core.db import Base
from app.core.enums import RiskLevel, RecommendedAction


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    user_id = Column(String, primary_key=True, index=True)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default=RiskLevel.LOW.value)
    recommended_action = Column(String, default=RecommendedAction.ALLOW.value)
    score_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
