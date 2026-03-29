from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from openclaw.api import health, webhook, projects
from openclaw.api import auth, dashboard, chat_ws
from openclaw.config import settings
from openclaw.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    # Clean up Redis connections
    from openclaw.queue import producer
    if producer._redis:
        await producer._redis.aclose()
    from openclaw.tools import messaging
    if messaging._pool:
        await messaging._pool.aclose()


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
_frontend_dir: Path | None = None
_frontend_candidates = [
    Path("/app/frontend/dist"),
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
]
for _candidate in _frontend_candidates:
    if _candidate.is_dir():
        _frontend_dir = _candidate
        break

if _frontend_dir:
    # Serve hashed JS/CSS bundles
    if (_frontend_dir / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=str(_frontend_dir / "assets")), name="static-assets")

    # SPA catch-all: serve static root files or fall back to index.html
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        file_path = _frontend_dir / full_path  # type: ignore[operator]
        if full_path and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_frontend_dir / "index.html"))  # type: ignore[operator]
