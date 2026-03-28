"""Vercel deployment client for creating and monitoring deployments."""

from __future__ import annotations

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

VERCEL_API = "https://api.vercel.com"


def _headers() -> dict:
    h = {
        "Authorization": f"Bearer {settings.VERCEL_TOKEN}",
        "Content-Type": "application/json",
    }
    if settings.VERCEL_TEAM_ID:
        h["x-vercel-team-id"] = settings.VERCEL_TEAM_ID
    return h


async def create_deployment(project_name: str, files: list[dict]) -> dict:
    """Create a Vercel deployment.

    Args:
        project_name: Name of the Vercel project.
        files: List of dicts with ``{"file": "path/to/file", "data": "file contents"}``.

    Returns:
        Deployment metadata including ``url`` and ``id``.
    """
    payload = {
        "name": project_name,
        "files": files,
        "projectSettings": {
            "framework": "nextjs",
        },
    }
    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(
            f"{VERCEL_API}/v13/deployments",
            json=payload,
            headers=_headers(),
        )
        response.raise_for_status()
        data = response.json()
        logger.info("deployment_created", url=data.get("url"), id=data.get("id"))
        return data


async def get_deployment_status(deployment_id: str) -> dict:
    """Check deployment status."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{VERCEL_API}/v13/deployments/{deployment_id}",
            headers=_headers(),
        )
        response.raise_for_status()
        return response.json()
