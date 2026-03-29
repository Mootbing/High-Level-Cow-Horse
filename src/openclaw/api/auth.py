"""Simple bearer token authentication for the dashboard."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from openclaw.config import settings

router = APIRouter()
_bearer = HTTPBearer(auto_error=False)


async def verify_dashboard_token(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """FastAPI dependency — validates Bearer token matches DASHBOARD_SECRET."""
    if creds is None or creds.credentials != settings.DASHBOARD_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
        )
    return creds.credentials


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    token: str


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Exchange the dashboard password for a bearer token."""
    if body.password != settings.DASHBOARD_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong password",
        )
    return LoginResponse(token=settings.DASHBOARD_SECRET)
