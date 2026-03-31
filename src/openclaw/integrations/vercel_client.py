"""Vercel client for creating projects and managing deployments."""

from __future__ import annotations

import httpx
import structlog

from openclaw.config import settings

logger = structlog.get_logger()

VERCEL_API = "https://api.vercel.com"


class VercelProtectionError(Exception):
    """Raised when Vercel deployment protection cannot be disabled."""


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


async def disable_protection(
    client: httpx.AsyncClient, project_name: str, max_retries: int = 3
) -> bool:
    """Disable all deployment protection so sites are publicly accessible.

    Retries up to max_retries times with 2s backoff.
    Raises VercelProtectionError if all retries fail.
    """
    import asyncio

    last_error = None
    for attempt in range(max_retries):
        if attempt > 0:
            await asyncio.sleep(2)
        try:
            resp = await client.patch(
                f"{VERCEL_API}/v9/projects/{project_name}",
                json={
                    "passwordProtection": None,
                    "trustedIps": None,
                    "ssoProtection": None,
                },
                headers=_headers(),
                params=_params(),
            )
            if resp.status_code in (200, 201):
                logger.info("vercel_protection_disabled", name=project_name)
                return True
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            logger.warning(
                "vercel_protection_disable_attempt_failed",
                name=project_name,
                attempt=attempt + 1,
                status=resp.status_code,
                body=resp.text[:200],
            )
        except Exception as e:
            last_error = str(e)
            logger.warning(
                "vercel_protection_disable_attempt_error",
                name=project_name,
                attempt=attempt + 1,
                error=str(e)[:200],
            )

    logger.error(
        "vercel_protection_disable_failed",
        name=project_name,
        last_error=last_error,
    )
    raise VercelProtectionError(
        f"Failed to disable protection for {project_name} after {max_retries} attempts: {last_error}"
    )


async def ensure_protection_disabled(project_name: str) -> bool:
    """Public convenience wrapper: disable all deployment protection.

    Creates its own httpx client. Returns True on success,
    raises VercelProtectionError on failure.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        return await disable_protection(client, project_name)


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
            # Disable deployment protection so sites are publicly accessible
            await disable_protection(client, project_name)
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
            await disable_protection(client, project_name)
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


async def get_latest_deployment(project_name: str, target: str = "production") -> dict | None:
    """Get the latest deployment for a project.

    target: "production" for main branch deploys, or omit/pass None for any (including previews).
    """
    async with httpx.AsyncClient(timeout=30) as client:
        params = {**_params(), "projectId": project_name, "limit": 1}
        if target:
            params["target"] = target
        resp = await client.get(
            f"{VERCEL_API}/v6/deployments",
            params=params,
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


async def deploy_directory(project_name: str, local_dir: str) -> dict:
    """Deploy a local directory to Vercel by uploading files directly.

    Uses Vercel's two-step process: upload files first, then create deployment.
    This bypasses the GitHub integration entirely.
    """
    import os
    import hashlib

    skip_dirs = {"node_modules", ".next", ".git", "__pycache__", ".vercel"}
    file_entries = []

    async with httpx.AsyncClient(timeout=300) as client:
        # Step 1: Upload each file to Vercel's file API
        for root, dirs, filenames in os.walk(local_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in filenames:
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, local_dir)
                with open(fpath, "rb") as f:
                    content = f.read()

                sha = hashlib.sha1(content).hexdigest()

                # Upload file blob
                upload_resp = await client.post(
                    f"{VERCEL_API}/v2/files",
                    content=content,
                    headers={
                        **_headers(),
                        "Content-Type": "application/octet-stream",
                        "x-vercel-digest": sha,
                    },
                    params=_params(),
                )
                # 200 = uploaded, 409 = already exists (both are fine)
                if upload_resp.status_code not in (200, 409):
                    logger.warning("vercel_file_upload_failed", file=rel_path, status=upload_resp.status_code)
                    continue

                file_entries.append({
                    "file": rel_path,
                    "sha": sha,
                    "size": len(content),
                })

        if not file_entries:
            return {"error": "No files to deploy"}

        # Step 2: Create deployment referencing uploaded files
        payload = {
            "name": project_name,
            "files": file_entries,
            "projectSettings": {"framework": "nextjs"},
            "target": "production",
        }

        resp = await client.post(
            f"{VERCEL_API}/v13/deployments",
            json=payload,
            headers=_headers(),
            params=_params(),
        )
        if resp.status_code not in (200, 201):
            logger.error("vercel_deploy_failed", status=resp.status_code, body=resp.text[:500])
            resp.raise_for_status()

        data = resp.json()
        url = data.get("url", "")
        logger.info("vercel_deployed", url=url, id=data.get("id"), files=len(file_entries))
        return {
            "url": f"https://{url}" if url else "",
            "id": data.get("id"),
            "readyState": data.get("readyState"),
            "files_deployed": len(file_entries),
        }
