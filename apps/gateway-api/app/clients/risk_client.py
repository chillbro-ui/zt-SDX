import logging

import httpx

from app.clients.config import RISK_URL

logger = logging.getLogger(__name__)


async def score_event(
    user_id: str,
    event: str,
    ip: str | None = None,
    geo: str | None = None,
    device_id: str | None = None,
    device_trust: float | None = None,
    sensitivity: str | None = None,
    is_vpn: bool = False,
    is_tor: bool = False,
    is_vm: bool = False,
    is_rooted: bool = False,
    is_new_fingerprint: bool = False,
    token: str | None = None,
) -> dict:
    """
    Send a telemetry event to risk-service for scoring.

    Returns the risk score result, or a safe default if the service is
    unavailable (fail-open — we don't block users on risk service outage).
    """
    payload = {
        "event": event,
        "user_id": user_id,
        "device_id": device_id,
        "ip": ip,
        "geo": geo,
        "sensitivity": sensitivity,
        "device_trust": device_trust,
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
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{RISK_URL}/risk/score",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning(f"risk_client.score_event failed (fail-open): {exc}")
        # Fail open — return a low-risk default so users aren't blocked
        return {
            "risk_score": 10,
            "level": "LOW",
            "recommended_action": "ALLOW",
            "rule_score": 0,
            "ml_score": 0,
            "fired_rules": [],
        }


async def get_user_risk(user_id: str, token: str | None = None) -> dict:
    """
    Fetch the current risk profile for a user.
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                f"{RISK_URL}/risk/user/{user_id}/profile",
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.warning(f"risk_client.get_user_risk failed: {exc}")
        return {
            "user_id": user_id,
            "risk_score": 0,
            "risk_level": "LOW",
            "recommended_action": "ALLOW",
            "score_count": 0,
        }
