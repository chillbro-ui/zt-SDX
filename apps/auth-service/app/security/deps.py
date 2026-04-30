from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.cache import rdb
from app.core.db import get_db
from app.security.token import verify_access_token
from app.services.user_service import get_user_by_id

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    payload = verify_access_token(token)
    user_id = payload.get("sub")

    # Check if this user has been logged out (token blacklisted)
    if rdb.get(f"revoked_user:{user_id}"):
        raise HTTPException(status_code=401, detail="Token has been revoked. Please log in again.")

    user = get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    if user.status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account suspended")

    return user
