from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.config import settings

security_scheme = HTTPBearer(auto_error=False)


def csrf_tokens_match(cookie: str | None, header: str | None) -> bool:
    import secrets

    return bool(cookie and header and secrets.compare_digest(cookie, header))


def decode_session_token(token: str) -> dict:
    """Decode and validate a console session with fixed issuer and audience."""
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    if payload.get("sub") != settings.admin_username:
        raise JWTError("Unknown user")
    return payload


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> str:
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return str(decode_session_token(token)["sub"])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc


async def require_csrf(request: Request) -> None:
    """Double-submit CSRF check for cookie-authenticated mutations."""
    cookie = request.cookies.get("csrf_token")
    header = request.headers.get("x-csrf-token")
    if not csrf_tokens_match(cookie, header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed")
