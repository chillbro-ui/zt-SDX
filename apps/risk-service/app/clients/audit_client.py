import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

AUDIT_URL = settings.AUDIT_URL


async def log_event(
    actor: str,
    action: str,
    resource: str,
    ip: str,
    result: str,
) -> None:
    """
    Fire-and-forget audit log call to audit-service.

    Failures are logged but never raised — audit logging must never
    block or break the scoring pipeline.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{AUDIT_URL}/audit/log",
                params={
                    "actor": actor,
                    "action": action,
                    "resource": resource,
                    "ip": ip,
                    "result": result,
                },
            )
    except Exception as exc:
        logger.warning(f"audit_client.log_event failed (non-fatal): {exc}")
