import logging
import os

import httpx

logger = logging.getLogger(__name__)

RISK_URL = os.getenv("RISK_URL", "http://risk-service:8000")


async def score_login_event(
    user_id: str,
    event: str,
    ip: str | None = None,
    device_id: str | None = None,
    device_trust: float | None = None,
    geo_distance_km: float | None = None,
    is_new_fingerprint: bool = False,
    is_vpn: bool = False,
    is_tor: bool = False,
    is_vm: bool = False,
    is_rooted: bool = False,
    token: str | None = None,
) -> dict:
    """
    Send a login-related telemetry event to risk-service.

    Called on: LOGIN_FAILED, LOGIN_SUCCESS, NEW_DEVICE_LOGIN, OTP_FAILED

    Returns the risk score result, or a safe default on failure (fail-open).
    The auth-service uses the returned risk_score and recommended_action
    to decide whether to allow, require MFA, or deny the login.
    """
    payload = {
        "event": event,
        "user_id": user_id,
        "device_id": device_id,
        "ip": ip,
        "geo": None,
        "sensitivity": None,
        "device_trust": device_trust,
        "geo_distance_km": geo_distance_km,
        "is_vpn": is_vpn,
        "is_tor": is_tor,
        "is_vm": is_vm,
        "is_rooted": is_rooted,
        "is_new_fingerprint": is_new_fingerprint,
    }

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                f"{RISK_URL}/risk/score",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning(f"risk_client.score_login_event failed (fail-open): {exc}")
        # Fail open — never block login due to risk-service outage
        return {
            "risk_score": 0,
            "level": "LOW",
            "recommended_action": "ALLOW",
            "rule_score": 0,
            "ml_score": 0,
            "fired_rules": [],
        }
