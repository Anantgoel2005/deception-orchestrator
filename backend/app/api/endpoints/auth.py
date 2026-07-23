from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from app.config import settings

router = APIRouter()
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=512)


class SessionOut(BaseModel):
    username: str
    csrf_token: str
    expires_at: datetime


def _password_is_valid(password: str) -> bool:
    if settings.admin_password_hash:
        return password_context.verify(password, settings.admin_password_hash)
    # Development-only convenience. Production configuration rejects it.
    return settings.deployment_mode == "development" and bool(settings.admin_password) and secrets.compare_digest(
        password, settings.admin_password
    )


def _set_session(response: Response, username: str) -> SessionOut:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.session_expire_minutes)
    token = jwt.encode({"sub": username, "exp": expires_at}, settings.secret_key, algorithm=settings.jwt_algorithm)
    csrf_token = secrets.token_urlsafe(32)
    secure = settings.deployment_mode == "production"
    response.set_cookie("access_token", token, httponly=True, secure=secure, samesite="lax", max_age=settings.session_expire_minutes * 60)
    response.set_cookie("csrf_token", csrf_token, httponly=False, secure=secure, samesite="lax", max_age=settings.session_expire_minutes * 60)
    return SessionOut(username=username, csrf_token=csrf_token, expires_at=expires_at)


@router.post("/login", response_model=SessionOut)
async def login(payload: LoginRequest, response: Response):
    if payload.username != settings.admin_username or not _password_is_valid(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return _set_session(response, payload.username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("csrf_token")


@router.get("/me", response_model=SessionOut)
async def current_session(request: Request):
    from app.api.dependencies import get_current_user

    username = await get_current_user(request, None)
    csrf_token = request.cookies.get("csrf_token")
    if not csrf_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is incomplete")
    return SessionOut(username=username, csrf_token=csrf_token, expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.session_expire_minutes))
