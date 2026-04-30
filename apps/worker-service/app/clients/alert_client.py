import requests


ALERT_URL = "http://alert-service:8000"


def create_alert(
    actor: str,
    severity: str,
    score_delta: int,
    details: str,
):
    response = requests.post(
        f"{ALERT_URL}/alerts/create",
        params={
            "type": "HIGH_RISK_FILE",
            "severity": severity,
            "actor": actor,
            "score_delta": score_delta,
            "details": details,
        },
    )

    return response.json()