"""FastAPI application for the Clarmi Dashboard API."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openclaw.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Clarmi Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.DASHBOARD_CORS_ORIGIN, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from openclaw.api.routers import (  # noqa: E402
    deployments,
    emails,
    knowledge,
    messages,
    metrics,
    projects,
    prospects,
    tasks,
)

app.include_router(prospects.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(emails.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(deployments.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
