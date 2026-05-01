import logging
import os

import requests

logger = logging.getLogger(__name__)

RISK_URL = os.getenv("RISK_URL", "http://risk-service:8000")


def score(
    owner_id: str,
    sensitivity: str = "INTERNAL",
    dlp_matched: bool = False,
) -> dict:
    """
    Send a FILE_UPLOAD telemetry event to risk-service after a DLP scan.

    The worker calls this once per file after scanning. We send FILE_UPLOAD
    (not FILE_DOWNLOAD) because this is a post-upload background scan.
    Sensitivity is passed so the risk-service can apply secret-file rules.

    If DLP matched, we still score — the risk-service will record the event
    and the worker will override the final status to QUARANTINED regardless.

    Returns a safe default if the service is unavailable (fail-open).
    """
    payload = {
        "event": "FILE_UPLOAD",
        "user_id": owner_id,
        "device_id": None,
        "ip": None,
        "geo": None,
        "sensitivity": sensitivity.upper() if sensitivity else "INTERNAL",
        "device_trust": None,
        "geo_distance_km": None,
        "is_vpn": False,
        "is_tor": False,
        "is_vm": False,
        "is_rooted": False,
        "is_new_fingerprint": False,
    }

    try:
        response = requests.post(
            f"{RISK_URL}/risk/score",
            json=payload,
            timeout=3,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "risk_score": data.get("risk_score", 0),
            "level": data.get("level", "LOW"),
            "recommended_action": data.get("recommended_action", "ALLOW"),
            "fired_rules": data.get("fired_rules", []),
        }
    except Exception as exc:
        logger.warning(f"risk_client.score failed (fail-open): {exc}")
        return {
            "risk_score": 10,
            "level": "LOW",
            "recommended_action": "ALLOW",
            "fired_rules": [],
        }
