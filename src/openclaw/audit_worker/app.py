"""Standalone FastAPI audit worker for the Clarmi website."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from openclaw.config import settings
from openclaw.db.session import async_session_factory
from openclaw.models.task import Task

# ---------------------------------------------------------------------------
# Rate limiting (in-memory, sufficient for single replica)
# ---------------------------------------------------------------------------

RATE_LIMIT_WINDOW = 3600  # 1 hour
RATE_LIMIT_MAX_PER_EMAIL = 3
RATE_LIMIT_MAX_PER_IP = 10

_rate_store: dict[str, list[float]] = {}


def _check_rate_limit(key: str, max_count: int) -> bool:
    """Return True if the request should be allowed."""
    now = datetime.now(timezone.utc).timestamp()
    cutoff = now - RATE_LIMIT_WINDOW
    hits = _rate_store.get(key, [])
    hits = [t for t in hits if t > cutoff]
    if len(hits) >= max_count:
        _rate_store[key] = hits
        return False
    hits.append(now)
    _rate_store[key] = hits
    return True


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class AuditRequest(BaseModel):
    url: str
    email: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        parsed = urlparse(v)
        if not parsed.netloc or "." not in parsed.netloc:
            raise ValueError("Invalid URL")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        import re

        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email address")
        return v


class AuditResponse(BaseModel):
    task_id: str
    message: str


# ---------------------------------------------------------------------------
# Lifespan — start background worker
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    from openclaw.audit_worker.worker import run_audit_worker

    task = asyncio.create_task(run_audit_worker())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Clarmi Audit Worker",
    version="1.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
# Add configured origins (production website domain, dashboard)
for origin in (settings.WEBSITE_CORS_ORIGIN, settings.DASHBOARD_CORS_ORIGIN):
    if origin and origin not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "audit-worker"}


@app.post("/api/v1/audit", response_model=AuditResponse, status_code=202)
async def submit_audit(body: AuditRequest, request: Request):
    # Rate limit by email
    email_key = f"email:{body.email.lower()}"
    if not _check_rate_limit(email_key, RATE_LIMIT_MAX_PER_EMAIL):
        raise HTTPException(429, "Too many requests for this email. Try again later.")

    # Rate limit by IP
    client_ip = request.headers.get(
        "x-forwarded-for", request.client.host if request.client else "unknown"
    )
    ip_key = f"ip:{client_ip}"
    if not _check_rate_limit(ip_key, RATE_LIMIT_MAX_PER_IP):
        raise HTTPException(429, "Too many requests. Try again later.")

    # Create the task
    async with async_session_factory() as session:
        task = Task(
            agent_type="website_audit",
            title=f"Website audit for {body.url}",
            input_data={"url": body.url, "email": str(body.email)},
            status="pending",
            priority=3,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        task_id = str(task.id)

    return AuditResponse(
        task_id=task_id,
        message="Your audit is being processed. Check your email shortly!",
    )
