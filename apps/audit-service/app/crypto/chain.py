import hashlib


def compute_hash(
    prev_hash: str,
    actor: str,
    action: str,
    resource: str,
    ip: str,
    result: str,
) -> str:
    payload = (
        f"{prev_hash}|"
        f"{actor}|"
        f"{action}|"
        f"{resource}|"
        f"{ip}|"
        f"{result}"
    )

    return hashlib.sha256(
        payload.encode()
    ).hexdigest()