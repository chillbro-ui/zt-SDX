import requests

RISK_URL = "http://risk-service:8000"


def score(file_id: str, owner_id: str) -> dict:
    """
    Placeholder — risk service is owned by another team.
    Returns a default low-risk score if the service is unavailable.
    """
    try:
        response = requests.post(
            f"{RISK_URL}/risk/score",
            params={"file_id": file_id, "owner_id": owner_id},
            timeout=2,
        )
        return response.json()
    except Exception:
        return {"risk_score": 10, "label": "LOW", "status": "ACTIVE"}
