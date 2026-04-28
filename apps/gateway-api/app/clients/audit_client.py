import httpx

from app.clients.config import AUDIT_URL


async def log(
    actor: str,
    action: str,
    resource: str,
    ip: str,
    result: str,
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUDIT_URL}/audit/log",
            params={
                "actor": actor,
                "action": action,
                "resource": resource,
                "ip": ip,
                "result": result,
            },
        )

    return response.json()