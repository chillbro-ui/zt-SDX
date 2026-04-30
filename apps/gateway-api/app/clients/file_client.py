from typing import Optional

import httpx

from app.clients.config import FILE_URL

# Large file uploads need a longer timeout — default 5s is too short for 100MB
UPLOAD_TIMEOUT = 120.0  # 2 minutes


async def upload(owner_id: str, filename: str, content: bytes, content_type: str):
    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT) as client:
        response = await client.post(
            f"{FILE_URL}/files/upload",
            params={"owner_id": owner_id},
            files={"file": (filename, content, content_type)},
        )
    return response.json()


async def list_files(owner_id: Optional[str] = None):
    async with httpx.AsyncClient() as client:
        params = {}
        if owner_id:
            params["owner_id"] = owner_id
        response = await client.get(f"{FILE_URL}/files/", params=params)
    return response.json()


async def get_file(file_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{FILE_URL}/files/{file_id}")
    return response.json()


async def download_file(file_id: str, user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{FILE_URL}/files/{file_id}/download",
            params={"user_id": user_id},
        )
    return response.json()


async def create_share(
    file_id: str,
    recipient_email: str,
    expiry_hours: int = 24,
    max_downloads: int = 1,
    device_lock: bool = False,
    watermark: bool = True,
):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{FILE_URL}/files/shares",
            params={
                "file_id": file_id,
                "recipient_email": recipient_email,
                "expiry_hours": expiry_hours,
                "max_downloads": max_downloads,
                "device_lock": device_lock,
                "watermark": watermark,
            },
        )
    return response.json()


async def download_via_share(share_token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{FILE_URL}/files/shares/{share_token}")
    return response.json()


async def delete_file(file_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{FILE_URL}/files/{file_id}")
    return response.json()
