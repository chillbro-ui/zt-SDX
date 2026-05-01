import json
from sqlalchemy.orm import Session

from app.core.cache import rdb
from app.features.schemas import FeatureVector
from app.models.risk_feature import RiskFeature


# How long to keep feature vectors in Redis (1 hour)
FEATURE_TTL_SECONDS = 3600

# Redis key pattern
def _redis_key(user_id: str) -> str:
    return f"features:{user_id}"


class FeatureStore:
    """
    Two-layer storage for feature vectors.

    Redis  → hot layer, fast lookup for scoring (TTL = 1 hour)
    Postgres → cold layer, full history for ML training

    Read path:  Redis first → fall back to Postgres if miss → return empty vector if new user
    Write path: always write to both
    """

    def __init__(self, db: Session):
        self.db = db

    async def get(self, user_id: str) -> FeatureVector:
        """Load a user's current feature vector. Redis first, then Postgres."""

        # 1. Try Redis
        raw = rdb.get(_redis_key(user_id))
        if raw:
            return FeatureVector(**json.loads(raw))

        # 2. Fall back to latest Postgres record
        row = (
            self.db.query(RiskFeature)
            .filter(RiskFeature.user_id == user_id)
            .order_by(RiskFeature.created_at.desc())
            .first()
        )
        if row:
            vector = FeatureVector(
                failed_logins_1h=row.failed_logins_1h,
                failed_logins_24h=row.failed_logins_24h,
                new_device=row.new_device,
                geo_distance_km=row.geo_distance_km,
                rapid_download_count=row.rapid_download_count,
                secret_file_accesses=row.secret_file_accesses,
                denied_attempts=row.denied_attempts,
                device_trust=row.device_trust,
            )
            # Warm up Redis for next time
            rdb.setex(_redis_key(user_id), FEATURE_TTL_SECONDS, vector.model_dump_json())
            return vector

        # 3. Brand new user — return default (all zeros)
        return FeatureVector()

    async def save(self, user_id: str, vector: FeatureVector, final_score: float = 0.0):
        """Persist a feature vector snapshot to both Redis and Postgres."""

        # Write to Redis (hot, with TTL)
        rdb.setex(_redis_key(user_id), FEATURE_TTL_SECONDS, vector.model_dump_json())

        # Write snapshot to Postgres (cold, permanent history for training)
        row = RiskFeature(
            user_id=user_id,
            failed_logins_1h=vector.failed_logins_1h,
            failed_logins_24h=vector.failed_logins_24h,
            new_device=vector.new_device,
            geo_distance_km=vector.geo_distance_km,
            rapid_download_count=vector.rapid_download_count,
            secret_file_accesses=vector.secret_file_accesses,
            denied_attempts=vector.denied_attempts,
            device_trust=vector.device_trust,
            final_score=final_score,
        )
        self.db.add(row)
        self.db.commit()

    async def clear(self, user_id: str):
        """Reset a user's feature vector (e.g. after a risk review resolves)."""
        rdb.delete(_redis_key(user_id))
