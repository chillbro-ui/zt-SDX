from typing import Optional

import httpx

from app.clients.config import AUTH_URL


async def create_org(
    name: str,
    domain: str,
    legal_name: Optional[str] = None,
    industry: Optional[str] = None,
    country: str = "IN",
    size: Optional[int] = None,
):
    async with httpx.AsyncClient() as client:
        params = {"name": name, "domain": domain, "country": country}
        if legal_name:
            params["legal_name"] = legal_name
        if industry:
            params["industry"] = industry
        if size:
            params["size"] = str(size)
        response = await client.post(f"{AUTH_URL}/orgs/", params=params)
    return response.json()


async def list_orgs():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_URL}/orgs/")
    return response.json()


async def get_org(org_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_URL}/orgs/{org_id}")
    return response.json()


async def get_departments(org_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{AUTH_URL}/orgs/{org_id}/departments")
    return response.json()


async def add_department(org_id: str, name: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/orgs/{org_id}/departments",
            params={"name": name},
        )
    return response.json()
