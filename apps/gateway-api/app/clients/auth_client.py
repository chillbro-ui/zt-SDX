from typing import Optional

import httpx

from app.clients.config import AUTH_URL


async def login(email: str, password: str, device_fingerprint: Optional[str] = None):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/auth/login",
            params={
                "email": email,
                "password": password,
                **({"device_fingerprint": device_fingerprint} if device_fingerprint else {}),
            },
        )
    return response.json()


async def verify_otp(challenge_id: str, otp: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/auth/verify-otp",
            params={"challenge_id": challenge_id, "otp": otp},
        )
    return response.json()


async def logout(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
    return response.json()


async def refresh_token(refresh_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/auth/refresh",
            params={"refresh_token": refresh_token},
        )
    return response.json()


async def provision_employee(org_id: str, email: str, role_name: str, department_name: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/auth/provision",
            params={
                "org_id": org_id,
                "email": email,
                "role_name": role_name,
                "department_name": department_name,
            },
        )
    return response.json()


async def activate_account(activation_code: str, password: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/auth/activate",
            params={"activation_code": activation_code, "password": password},
        )
    return response.json()


async def me(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUTH_URL}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    if response.status_code != 200:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Authentication failed"),
        )
    return response.json()
