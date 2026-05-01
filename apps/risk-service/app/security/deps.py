from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security.token import verify_access_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validates the Bearer JWT token on every protected request.

    Returns the decoded token payload (contains sub, role, org_id, etc.).
    The risk-service is stateless with respect to users — it trusts the
    JWT signed by auth-service rather than hitting the DB for every call.

    Raises:
        401 — missing / invalid / expired token
    """
    token = credentials.credentials
    payload = verify_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing subject claim")

    return payload


def get_service_or_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Looser dependency used on the /score endpoint.

    The /score endpoint is called by:
      - gateway-api (on behalf of a real user)
      - worker-service (background job, uses a service token)

    Both must present a valid JWT. We just verify the signature and
    return the payload — callers embed user_id in the request body anyway.
    """
    token = credentials.credentials
    payload = verify_access_token(token)
    return payload
