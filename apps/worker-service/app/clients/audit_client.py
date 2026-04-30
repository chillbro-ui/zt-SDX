import requests


AUDIT_URL = "http://audit-service:8000"


def log(
    actor: str,
    action: str,
    resource: str,
    result: str,
):
    response = requests.post(
        f"{AUDIT_URL}/audit/log",
        params={
            "actor": actor,
            "action": action,
            "resource": resource,
            "ip": "worker",
            "result": result,
        },
    )

    return response.json()