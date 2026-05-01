import logging
from sqlalchemy.orm import Session

from app.clients import alert_client, audit_client
from app.features.schemas import TelemetryEvent
from app.features.extractor import FeatureExtractor
from app.features.store import FeatureStore
from app.scoring.scorer import scorer, ScoreResult
from app.anomaly.detector import detector
from app.models.risk_profile import RiskProfile
from app.models.risk_event import RiskEvent
from app.models.alert import Alert

logger = logging.getLogger(__name__)


class RiskService:
    """
    Main orchestrator for the risk scoring pipeline.

    Given a telemetry event it:
        1. Extracts / updates the user's feature vector
        2. Scores it (rules + ML blend)
        3. Detects named anomaly alerts
        4. Persists everything to Postgres
        5. Forwards detected alerts to alert-service
        6. Returns the score result

    The API layer handles audit logging so this class stays focused on scoring.
    """

    def __init__(self, db: Session):
        self.db = db
        self.store = FeatureStore(db)
        self.extractor = FeatureExtractor(self.store)

    async def process_event(self, event: TelemetryEvent) -> ScoreResult:
        # 1. Extract features from this event (updates the user's running vector)
        vector = await self.extractor.extract(event)

        # 2. Score the vector
        result = scorer.score(vector)

        # 3. Detect any named anomaly alerts
        alerts = detector.detect(event.user_id, vector)

        # 4. Persist everything to Postgres
        await self._persist_event(event, result)
        await self._upsert_profile(event.user_id, result)
        await self._persist_alerts(event.user_id, alerts)

        # 5. Save feature snapshot with the final score attached
        await self.store.save(event.user_id, vector, final_score=result.final_score)

        # 6. Forward detected alerts to alert-service (fire-and-forget)
        for a in alerts:
            await alert_client.create_alert(
                actor=event.user_id,
                alert_type=a.alert_type.value,
                severity=a.severity.value,
                score_delta=a.score_delta,
                details=a.description,
            )

        logger.info(
            f"user={event.user_id} event={event.event} "
            f"rule={result.rule_score} ml={result.ml_score} "
            f"final={result.final_score} level={result.level} "
            f"alerts={len(alerts)}"
        )

        return result

    async def get_profile(self, user_id: str) -> RiskProfile | None:
        return (
            self.db.query(RiskProfile)
            .filter(RiskProfile.user_id == user_id)
            .first()
        )

    # ── Private helpers ──────────────────────────────────────────────────────

    async def _persist_event(self, event: TelemetryEvent, result: ScoreResult):
        row = RiskEvent(
            user_id=event.user_id,
            event_type=event.event.value,   # store string, not enum object
            payload=event.model_dump(mode="json"),
            rule_score=result.rule_score,
            ml_score=result.ml_score,
            final_score=result.final_score,
            ip=event.ip,
            geo=event.geo,
        )
        self.db.add(row)
        self.db.commit()

    async def _upsert_profile(self, user_id: str, result: ScoreResult):
        """Update existing profile or create one if this is the first event for this user."""
        profile = (
            self.db.query(RiskProfile)
            .filter(RiskProfile.user_id == user_id)
            .first()
        )
        if profile:
            profile.risk_score = result.final_score
            profile.risk_level = result.level.value              # store string
            profile.recommended_action = result.recommended_action.value  # store string
            profile.score_count += 1
        else:
            profile = RiskProfile(
                user_id=user_id,
                risk_score=result.final_score,
                risk_level=result.level.value,                   # store string
                recommended_action=result.recommended_action.value,  # store string
                score_count=1,
            )
            self.db.add(profile)
        self.db.commit()

    async def _persist_alerts(self, user_id: str, alerts: list):
        """Persist detected alerts to the local risk DB for history."""
        for a in alerts:
            row = Alert(
                user_id=user_id,
                alert_type=a.alert_type.value,   # store string, not enum object
                severity=a.severity.value,        # store string, not enum object
                score_delta=a.score_delta,
                description=a.description,
            )
            self.db.add(row)
        if alerts:
            self.db.commit()
