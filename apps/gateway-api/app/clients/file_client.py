from typing import Optional

import httpx
from fastapi.responses import Response

from app.clients.config import FILE_URL

# Large file uploads need a longer timeout
UPLOAD_TIMEOUT = 120.0


async def upload(owner_id: str, filename: str, content: bytes, content_type: str, sensitivity: str = "INTERNAL"):
    async with httpx.AsyncClient(timeout=UPLOAD_TIMEOUT) as client:
        response = await client.post(
            f"{FILE_URL}/files/upload",
            params={"owner_id": owner_id, "sensitivity": sensitivity},
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
    """Download and decrypt file — returns a FastAPI Response to stream to client."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{FILE_URL}/files/{file_id}/download",
            params={"user_id": user_id},
        )
    if response.status_code != 200:
        return response.json()

    return Response(
        content=response.content,
        media_type=response.headers.get("content-type", "application/octet-stream"),
        headers={
            "Content-Disposition": response.headers.get("content-disposition", ""),
            "X-Watermark": response.headers.get("x-watermark", ""),
            "X-SHA256": response.headers.get("x-sha256", ""),
        },
    )


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
    """Download via share token — returns a FastAPI Response to stream to client."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(f"{FILE_URL}/files/shares/{share_token}")

    if response.status_code != 200:
        return response.json()

    return Response(
        content=response.content,
        media_type=response.headers.get("content-type", "application/octet-stream"),
        headers={
            "Content-Disposition": response.headers.get("content-disposition", ""),
            "X-Watermark": response.headers.get("x-watermark", ""),
            "X-SHA256": response.headers.get("x-sha256", ""),
        },
    )


async def delete_file(file_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{FILE_URL}/files/{file_id}")
    return response.json()
