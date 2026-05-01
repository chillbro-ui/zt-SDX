"""
Role-based access control for gateway endpoints.

Usage:
    user: dict = Depends(require_roles(["SUPER_ADMIN", "SECURITY_ADMIN"]))
    user: dict = Depends(require_min_privilege(75))
"""

from typing import List

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.clients import auth_client

_bearer = HTTPBearer()

# Role privilege levels
PRIVILEGE = {
    "SUPER_ADMIN": 100,
    "SECURITY_ADMIN": 90,
    "DEPT_HEAD": 75,
    "MANAGER": 60,
    "AUDITOR": 50,
    "EMPLOYEE": 20,
}


def require_roles(allowed_roles: List[str]):
    """Dependency: user must have one of the specified roles."""
    async def _check(
        credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    ) -> dict:
        token = credentials.credentials
        user = await auth_client.me(token)
        role = user.get("role", "")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required: {', '.join(allowed_roles)}. Your role: {role}",
            )
        return user
    return _check


def require_min_privilege(min_level: int):
    """Dependency: user must have at least min_level privilege."""
    async def _check(
        credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    ) -> dict:
        token = credentials.credentials
        user = await auth_client.me(token)
        role = user.get("role", "")
        level = PRIVILEGE.get(role, 0)
        if level < min_level:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Min privilege {min_level} required. '{role}' has {level}.",
            )
        return user
    return _check
