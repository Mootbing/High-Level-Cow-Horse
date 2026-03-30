"""JWT-based authentication for the dashboard."""

from __future__ import annotations

import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from openclaw.config import settings

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)


def _jwt_secret() -> str:
    return settings.JWT_SECRET or settings.DASHBOARD_SECRET


def create_access_token() -> str:
    """Create a signed JWT with an expiry."""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": "dashboard",
        "iat": now,
        "exp": now + datetime.timedelta(hours=settings.JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


async def verify_dashboard_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """FastAPI dependency — validates JWT Bearer token."""
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )
    try:
        payload = jwt.decode(creds.credentials, _jwt_secret(), algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Exchange the dashboard password for a JWT."""
    if body.password != settings.DASHBOARD_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong password",
        )
    return LoginResponse(token=create_access_token())
