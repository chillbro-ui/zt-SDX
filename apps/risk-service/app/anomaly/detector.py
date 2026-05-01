from dataclasses import dataclass

from app.core.enums import AlertType, AlertSeverity
from app.features.schemas import FeatureVector


@dataclass
class DetectedAlert:
    alert_type: AlertType
    severity: AlertSeverity
    score_delta: float
    description: str


class AnomalyDetector:
    """
    Pattern-based alert engine. Separate from the rule engine.

    The rule engine produces a SCORE.
    The anomaly detector produces named ALERTS.

    Why separate? Because alerts are human-readable events stored for
    security teams. The rule engine just adds numbers. An alert says
    "hey, this specific dangerous thing happened" with a name and description.

    Each check is independent — multiple alerts can fire for one event.
    """

    def detect(self, user_id: str, vector: FeatureVector) -> list[DetectedAlert]:
        alerts = []

        alerts.extend(self._check_brute_force(vector))
        alerts.extend(self._check_rapid_download(vector))
        alerts.extend(self._check_impossible_travel(vector))
        alerts.extend(self._check_sensitive_exfiltration(vector))
        alerts.extend(self._check_privilege_escalation(vector))
        alerts.extend(self._check_suspicious_device(vector))

        return alerts

    # ── Individual checks ────────────────────────────────────────────────────

    def _check_brute_force(self, v: FeatureVector) -> list[DetectedAlert]:
        if v.failed_logins_1h >= 5:
            return [DetectedAlert(
                alert_type=AlertType.BRUTE_FORCE_LOGIN,
                severity=AlertSeverity.HIGH if v.failed_logins_1h < 10 else AlertSeverity.CRITICAL,
                score_delta=25.0,
                description=f"{v.failed_logins_1h} failed login attempts in the last hour."
            )]
        return []

    def _check_rapid_download(self, v: FeatureVector) -> list[DetectedAlert]:
        if v.rapid_download_count >= 10:
            return [DetectedAlert(
                alert_type=AlertType.RAPID_DOWNLOAD,
                severity=AlertSeverity.HIGH,
                score_delta=35.0,
                description=f"{v.rapid_download_count} file downloads in a short window — possible bulk exfiltration."
            )]
        return []

    def _check_impossible_travel(self, v: FeatureVector) -> list[DetectedAlert]:
        if v.geo_distance_km >= 5000:
            return [DetectedAlert(
                alert_type=AlertType.IMPOSSIBLE_TRAVEL,
                severity=AlertSeverity.CRITICAL,
                score_delta=35.0,
                description=f"Login from {v.geo_distance_km:.0f} km away — physically impossible travel detected."
            )]
        return []

    def _check_sensitive_exfiltration(self, v: FeatureVector) -> list[DetectedAlert]:
        if v.secret_file_accesses >= 3:
            return [DetectedAlert(
                alert_type=AlertType.HIGH_SENSITIVITY_EXFILTRATION,
                severity=AlertSeverity.HIGH,
                score_delta=25.0,
                description=f"{v.secret_file_accesses} accesses to SECRET sensitivity files detected."
            )]
        return []

    def _check_privilege_escalation(self, v: FeatureVector) -> list[DetectedAlert]:
        if v.denied_attempts >= 3:
            return [DetectedAlert(
                alert_type=AlertType.PRIVILEGE_ESCALATION,
                severity=AlertSeverity.MEDIUM,
                score_delta=30.0,
                description=f"{v.denied_attempts} policy denial attempts — possible privilege escalation."
            )]
        return []

    def _check_suspicious_device(self, v: FeatureVector) -> list[DetectedAlert]:
        if v.device_trust < 30:
            return [DetectedAlert(
                alert_type=AlertType.SUSPICIOUS_SHARING,  # re-using closest enum
                severity=AlertSeverity.HIGH,
                score_delta=20.0,
                description=f"Very low device trust score ({v.device_trust}) — TOR/rooted/compromised device suspected."
            )]
        return []


# Singleton
detector = AnomalyDetector()
