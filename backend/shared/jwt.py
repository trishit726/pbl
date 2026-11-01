"""JWT verification helpers for user and service access tokens."""

from datetime import timedelta
from typing import Any

import jwt as jose_jwt
from jwt import InvalidTokenError

from .config import get_settings


def verify_token(token: str, *, expected_type: str = "access") -> dict[str, Any]:
    """Verify signature, issuer, audience, expiry and token class."""
    settings = get_settings()
    claims = jose_jwt.decode(
        token,
        settings.jwt_signing_key,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        options={"require": ["exp", "iat", "iss", "aud", "sub", "token_type"]},
        leeway=timedelta(seconds=0),
    )
    if claims.get("token_type") != expected_type:
        raise InvalidTokenError("Unexpected token type")
    if expected_type in {"access", "service"}:
        required = ("user_id", "role", "device_id", "session_id") if expected_type == "access" else ("service_id",)
        if any(not claims.get(field) for field in required):
            raise InvalidTokenError("Required token claim is missing")
    return claims

