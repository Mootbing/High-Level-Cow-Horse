from contextlib import asynccontextmanager

from fastapi import FastAPI

from openclaw.api import health, webhook, projects
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

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(webhook.router, prefix="/api", tags=["webhook"])
app.include_router(projects.router, prefix="/api", tags=["projects"])
