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
    Fetch raw file bytes from the file-service for DLP scanning.
    The file-service returns a presigned MinIO URL; we then fetch the bytes.
    """
    # Get presigned URL from file-service using stored_name
    response = requests.get(
        f"{FILE_URL}/files/content/{stored_name}",
        timeout=10,
    )
    if response.status_code != 200:
        return b""
    data = response.json()
    download_url = data.get("download_url", "")
    if not download_url:
        return b""

    # Fetch actual bytes from MinIO presigned URL
    file_response = requests.get(download_url, timeout=30)
    if file_response.status_code != 200:
        return b""
    return file_response.content
