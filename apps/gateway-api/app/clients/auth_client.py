import httpx

from app.clients.config import AUTH_URL


async def login(
    email: str,
    password: str,
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_URL}/auth/login",
            params={
                "email": email,
                "password": password,
            },
        )

    return response.json()


async def me(
    token: str,
):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AUTH_URL}/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    return response.json()