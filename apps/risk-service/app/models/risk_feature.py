from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.db import Base

class RiskFeature(Base):
    __tablename__ = "risk_features"

    id = Column(String, primary_key=True, default=lambda: __import__('uuid').uuid4().hex)
    user_id = Column(String, index=True)
    failed_logins_1h = Column(Float, default=0.0)
    failed_logins_24h = Column(Float, default=0.0)
    new_device = Column(Float, default=0.0)
    geo_distance_km = Column(Float, default=0.0)
    rapid_download_count = Column(Float, default=0.0)
    secret_file_accesses = Column(Float, default=0.0)
    denied_attempts = Column(Float, default=0.0)
    device_trust = Column(Float, default=100.0)
    final_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())