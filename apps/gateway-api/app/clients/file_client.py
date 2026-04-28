import httpx

from app.clients.config import FILE_URL


async def upload(
    owner_id: str,
    filename: str,
    content: bytes,
    content_type: str,
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FILE_URL}/files/upload",
            params={
                "owner_id": owner_id,
            },
            files={
                "file": (
                    filename,
                    content,
                    content_type,
                )
            },
        )

    return response.json()