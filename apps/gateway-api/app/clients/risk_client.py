import httpx

from app.clients.config import RISK_URL


async def score(file_id: str, owner_id: str) -> dict:
    """
    Placeholder — risk service is owned by another team.
    Returns a default low-risk score if the service is unavailable.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                f"{RISK_URL}/risk/score",
                params={"file_id": file_id, "owner_id": owner_id},
            )
        return response.json()
    except Exception:
        # Risk service unavailable — default to low risk (fail open for uploads)
        return {"risk_score": 10, "label": "LOW", "status": "ACTIVE"}
