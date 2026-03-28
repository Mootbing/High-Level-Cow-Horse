"""Vercel client for creating projects linked to GitHub repos and managing deployments."""

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


async def create_project_from_github(
    project_name: str, github_repo: str, framework: str = "nextjs"
) -> dict:
    """Create a Vercel project linked to a GitHub repo for auto-deploys.

    Args:
        project_name: Vercel project name (used in the URL).
        github_repo: Full GitHub repo name (e.g., "openclaw-bot/cryptovault").
        framework: Framework preset (default: nextjs).

    Returns:
        Project metadata including id, name, and link info.
    """
    owner, repo = github_repo.split("/", 1)

    # First check if project already exists
    async with httpx.AsyncClient(timeout=30) as client:
        check = await client.get(
            f"{VERCEL_API}/v9/projects/{project_name}",
            headers=_headers(),
        )
        if check.status_code == 200:
            logger.info("vercel_project_exists", name=project_name)
            return check.json()

    # Create project linked to GitHub
    async with httpx.AsyncClient(timeout=30) as client:
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
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("vercel_project_created", name=data.get("name"), id=data.get("id"))
        return data


async def trigger_deployment(project_name: str) -> dict:
    """Trigger a new deployment for a Vercel project (after a git push)."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{VERCEL_API}/v13/deployments",
            json={"name": project_name, "target": "production"},
            headers=_headers(),
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
        )
        resp.raise_for_status()
        return resp.json()


async def get_latest_deployment(project_name: str) -> dict | None:
    """Get the latest deployment for a project."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{VERCEL_API}/v6/deployments",
            params={"projectId": project_name, "limit": 1, "target": "production"},
            headers=_headers(),
        )
        resp.raise_for_status()
        deployments = resp.json().get("deployments", [])
        return deployments[0] if deployments else None


async def create_deployment(project_name: str, files: list[dict]) -> dict:
    """Create a Vercel deployment by uploading files directly (legacy, non-GitHub flow)."""
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
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("deployment_created", url=data.get("url"), id=data.get("id"))
        return data
