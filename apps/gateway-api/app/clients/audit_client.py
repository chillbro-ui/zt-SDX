import httpx

from app.clients.config import AUDIT_URL


async def log(actor: str, action: str, resource: str, ip: str, result: str):
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


async def list_events(limit: int = 100, offset: int = 0):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUDIT_URL}/audit/logs",
            params={"limit": limit, "offset": offset},
        )
    return response.json()


async def verify_chain():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUDIT_URL}/audit/verify")
    return response.json()
