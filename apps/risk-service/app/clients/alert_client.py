import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ALERT_URL = settings.ALERT_URL


async def create_alert(
    actor: str,
    alert_type: str,
    severity: str,
    score_delta: float,
    details: str,
) -> None:
    """
    Forward a detected anomaly alert to the alert-service.

    Failures are logged but never raised — alert forwarding must never
    block or break the scoring pipeline.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{ALERT_URL}/alerts/create",
                params={
                    "type": alert_type,
                    "severity": severity,
                    "actor": actor,
                    "score_delta": int(score_delta),
                    "details": details,
                },
            )
    except Exception as exc:
        logger.warning(f"alert_client.create_alert failed (non-fatal): {exc}")
