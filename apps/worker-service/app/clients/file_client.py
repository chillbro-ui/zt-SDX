import requests

FILE_URL = "http://file-service:8000"


def update_risk(file_id: str, risk_score: int, status: str):
    response = requests.patch(
        f"{FILE_URL}/files/{file_id}/risk",
        params={"risk_score": risk_score, "status": status},
    )
    return response.json()


def get_file_content(stored_name: str) -> bytes:
    """
    Fetch decrypted file bytes from file-service for DLP scanning.
    The file-service handles decryption internally.
    """
    response = requests.get(
        f"{FILE_URL}/files/content/{stored_name}",
        timeout=30,
    )
    if response.status_code != 200:
        return b""
    return response.content
