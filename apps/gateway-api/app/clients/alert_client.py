import httpx

from app.clients.config import ALERT_URL


async def list_alerts(limit: int = 100, offset: int = 0):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ALERT_URL}/alerts/",
            params={"limit": limit, "offset": offset},
        )
    return response.json()
