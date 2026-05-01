from app.core.enums import EventType
from app.features.schemas import TelemetryEvent, FeatureVector
from app.features.store import FeatureStore


class FeatureExtractor:
    """
    Reads a telemetry event and updates the user's feature vector.

    Think of this as the translator — raw events come in, meaningful
    numbers come out. Those numbers are what the scoring engine uses.

    It doesn't score anything. It only extracts and accumulates features.
    """

    def __init__(self, store: FeatureStore):
        self.store = store

    async def extract(self, event: TelemetryEvent) -> FeatureVector:
        """
        Load the user's current feature vector from the store,
        apply the delta from this event, and return the updated vector.

        NOTE: We do NOT persist here. The caller (RiskService) persists
        once after scoring so the final_score is included in the snapshot.
        """
        vector = await self.store.get(event.user_id)
        vector = self._apply_event(vector, event)
        return vector

    def _apply_event(self, vector: FeatureVector, event: TelemetryEvent) -> FeatureVector:
        """
        Mutate the feature vector based on what kind of event arrived.
        Each event type touches different feature fields.
        """
        data = vector.model_dump()

        # ── AUTH EVENTS ──────────────────────────────────────────────────────
        if event.event == EventType.LOGIN_FAILED:
            data["failed_logins_1h"] += 1
            data["failed_logins_24h"] += 1

        elif event.event == EventType.OTP_FAILED:
            # OTP failure is a weaker signal than login failure
            data["failed_logins_1h"] += 1

        elif event.event == EventType.NEW_DEVICE_LOGIN:
            data["new_device"] = 1
            if event.device_trust is not None:
                data["device_trust"] = event.device_trust
            if event.geo_distance_km is not None:
                data["geo_distance_km"] = event.geo_distance_km

        elif event.event == EventType.LOGIN_SUCCESS:
            # Successful login resets short-term failure counter
            data["failed_logins_1h"] = 0
            if event.device_trust is not None:
                data["device_trust"] = event.device_trust
            if event.geo_distance_km is not None:
                data["geo_distance_km"] = event.geo_distance_km

        # ── FILE EVENTS ──────────────────────────────────────────────────────
        elif event.event == EventType.FILE_DOWNLOAD:
            data["rapid_download_count"] += 1
            if event.sensitivity == "SECRET":
                data["secret_file_accesses"] += 1

        elif event.event == EventType.FILE_UPLOAD:
            if event.sensitivity == "SECRET":
                data["secret_file_accesses"] += 1

        elif event.event == EventType.SHARE_CREATED:
            # External shares are tracked via denied_attempts if they get blocked
            # Otherwise just bump download count as a signal
            data["rapid_download_count"] += 1

        # ── POLICY EVENTS ─────────────────────────────────────────────────────
        elif event.event == EventType.POLICY_DENY:
            data["denied_attempts"] += 1

        elif event.event == EventType.MFA_ESCALATED:
            # MFA being forced is a mild signal something looked suspicious upstream
            data["denied_attempts"] += 1

        # ── DEVICE SIGNALS (can come with any event) ─────────────────────────
        # Apply device trust degradation if suspicious signals are present
        if event.is_vpn:
            data["device_trust"] = min(data["device_trust"], 70)
        if event.is_tor:
            data["device_trust"] = min(data["device_trust"], 20)
        if event.is_vm:
            data["device_trust"] = min(data["device_trust"], 50)
        if event.is_rooted:
            data["device_trust"] = min(data["device_trust"], 40)
        if event.is_new_fingerprint:
            data["new_device"] = 1
            data["device_trust"] = min(data["device_trust"], 60)

        return FeatureVector(**data)
