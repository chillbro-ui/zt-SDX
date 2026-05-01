from fastapi import HTTPException
from jose import JWTError, jwt

from app.core.config import settings


def verify_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    Raises HTTP 401 if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
