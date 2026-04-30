import httpx

from app.clients.config import POLICY_URL


async def evaluate(
    role: str,
    resource: str,
    action: str,
    clearance_level: int = 1,
    risk_score: int = 0,
    device_trusted: bool = False,
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{POLICY_URL}/policy/evaluate",
            params={
                "role": role,
                "resource": resource,
                "action": action,
                "clearance_level": clearance_level,
                "risk_score": risk_score,
                "device_trusted": device_trusted,
            },
        )
    return response.json()
