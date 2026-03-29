import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from openclaw.api import health, webhook, projects
from openclaw.api import auth, dashboard, chat_ws
from openclaw.config import settings
from openclaw.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# API routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(webhook.router, prefix="/api", tags=["webhook"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(chat_ws.router, tags=["chat"])

# Serve frontend SPA (must be last — catches all non-API routes)
# Try multiple paths: /app/frontend/dist (Docker), or relative to source
_frontend_candidates = [
    Path("/app/frontend/dist"),
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
]
for _candidate in _frontend_candidates:
    if _candidate.is_dir():
        app.mount("/", StaticFiles(directory=str(_candidate), html=True), name="frontend")
        break
