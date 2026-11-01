"""Plain role-based authorization dependencies; no risk or trust scoring."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from .jwt import verify_token

bearer_scheme = HTTPBearer(auto_error=False)
VALID_ROLES = frozenset({"student", "faculty", "admin"})


def current_principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    try:
        claims = verify_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token") from exc
    if claims.get("role") not in VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown role")
    return claims


def require_roles(*roles: str) -> Callable:
    """Require any listed role. Ownership/resource checks remain service-level."""
    invalid = set(roles) - VALID_ROLES
    if invalid:
        raise ValueError(f"Unsupported roles: {', '.join(sorted(invalid))}")

    def dependency(principal: dict = Depends(current_principal)) -> dict:
        if principal["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return dependency

