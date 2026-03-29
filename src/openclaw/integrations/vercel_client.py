"""Vercel client for creating projects and managing deployments."""

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
    return h


def _params() -> dict:
    """Add teamId query param if set."""
    p = {}
    if settings.VERCEL_TEAM_ID:
        p["teamId"] = settings.VERCEL_TEAM_ID
    return p


async def create_project_from_github(
    project_name: str, github_repo: str, framework: str = "nextjs"
) -> dict:
    """Create a Vercel project linked to a GitHub repo for auto-deploys."""
    async with httpx.AsyncClient(timeout=30) as client:
        # Check if project already exists
        check = await client.get(
            f"{VERCEL_API}/v9/projects/{project_name}",
            headers=_headers(),
            params=_params(),
        )
        if check.status_code == 200:
            logger.info("vercel_project_exists", name=project_name)
            return check.json()

        # Try to create with GitHub link
        # First, try the simple name-based approach
        resp = await client.post(
            f"{VERCEL_API}/v10/projects",
            json={
                "name": project_name,
                "framework": framework,
                "gitRepository": {
                    "repo": github_repo,
                    "type": "github",
                },
            },
            headers=_headers(),
            params=_params(),
        )

        if resp.status_code == 200 or resp.status_code == 201:
            data = resp.json()
            logger.info("vercel_project_created", name=data.get("name"), id=data.get("id"))
            return data

        # If GitHub link fails (needs installation ID), create without it
        logger.warning("vercel_github_link_failed", status=resp.status_code, body=resp.text[:200])
        resp2 = await client.post(
            f"{VERCEL_API}/v10/projects",
            json={
                "name": project_name,
                "framework": framework,
            },
            headers=_headers(),
            params=_params(),
        )
        if resp2.status_code in (200, 201):
            data = resp2.json()
            logger.info("vercel_project_created_no_git", name=data.get("name"))
            return data

        resp2.raise_for_status()
        return {}


async def trigger_deployment(project_name: str) -> dict:
    """Trigger a new deployment for a Vercel project."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{VERCEL_API}/v13/deployments",
            json={"name": project_name, "target": "production"},
            headers=_headers(),
            params=_params(),
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("deployment_triggered", url=data.get("url"), id=data.get("id"))
        return data


async def get_deployment_status(deployment_id: str) -> dict:
    """Check deployment status."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{VERCEL_API}/v13/deployments/{deployment_id}",
            headers=_headers(),
            params=_params(),
        )
        resp.raise_for_status()
        return resp.json()


async def get_latest_deployment(project_name: str) -> dict | None:
    """Get the latest deployment for a project."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{VERCEL_API}/v6/deployments",
            params={**_params(), "projectId": project_name, "limit": 1, "target": "production"},
            headers=_headers(),
        )
        resp.raise_for_status()
        deployments = resp.json().get("deployments", [])
        return deployments[0] if deployments else None


async def delete_project(project_name: str) -> bool:
    """Delete a Vercel project. Returns True if deleted."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.delete(
            f"{VERCEL_API}/v9/projects/{project_name}",
            headers=_headers(),
            params=_params(),
        )
        if resp.status_code in (200, 204):
            logger.info("vercel_project_deleted", name=project_name)
            return True
        logger.warning("vercel_delete_failed", name=project_name, status=resp.status_code)
        return False


async def create_deployment(project_name: str, files: list[dict]) -> dict:
    """Create a Vercel deployment by uploading files directly."""
    payload = {
        "name": project_name,
        "files": files,
        "projectSettings": {"framework": "nextjs"},
    }
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{VERCEL_API}/v13/deployments",
            json=payload,
            headers=_headers(),
            params=_params(),
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("deployment_created", url=data.get("url"), id=data.get("id"))
        return data
