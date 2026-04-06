"""Deployment API routes."""

from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from openclaw.config import settings
from openclaw.db.deps import DBSession
from openclaw.models.deployment import Deployment
from openclaw.models.project import Project
from openclaw.api.schemas.deployments import DeploymentRead

router = APIRouter(tags=["deployments"])

GITHUB_API = "https://api.github.com"
VERCEL_API = "https://api.vercel.com"


@router.get("/projects/{project_id}/deployments", response_model=list[DeploymentRead])
async def list_project_deployments(session: DBSession, project_id: UUID):
    stmt = (
        select(Deployment)
        .where(Deployment.project_id == project_id)
        .order_by(Deployment.created_at.desc())
    )
    result = await session.execute(stmt)
    return [DeploymentRead.model_validate(d) for d in result.scalars().all()]


@router.post("/projects/{project_id}/rollback")
async def rollback_deployment(session: DBSession, project_id: UUID, body: dict):
    """Promote an older Vercel deployment to production (rollback)."""
    from openclaw.integrations.vercel_client import promote_deployment

    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    deployment_id = body.get("deployment_id")
    if not deployment_id:
        raise HTTPException(400, "deployment_id required")

    meta = project.metadata_ or {}
    vercel_project = meta.get("vercel_project") or project.slug

    ok = await promote_deployment(vercel_project, deployment_id)
    if not ok:
        raise HTTPException(502, "Failed to promote deployment on Vercel")

    return {"ok": True, "promoted_deployment_id": deployment_id}


@router.get("/projects/{project_id}/history")
async def get_project_history(session: DBSession, project_id: UUID):
    """Fetch git commit history + Vercel deployments for a project."""
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    meta = project.metadata_ or {}
    github_repo = meta.get("github_repo")
    vercel_project = meta.get("vercel_project")

    if not github_repo:
        return {"commits": [], "branches": []}

    gh_headers = {
        "Authorization": f"Bearer {settings.GITHUB_PAT}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # Fetch branches
        branches_resp = await client.get(
            f"{GITHUB_API}/repos/{github_repo}/branches",
            headers=gh_headers,
            params={"per_page": 20},
        )
        branches = []
        if branches_resp.status_code == 200:
            branches = [b["name"] for b in branches_resp.json()]

        # Fetch commits from all branches
        all_commits = {}
        for branch in branches or ["main"]:
            commits_resp = await client.get(
                f"{GITHUB_API}/repos/{github_repo}/commits",
                headers=gh_headers,
                params={"sha": branch, "per_page": 50},
            )
            if commits_resp.status_code != 200:
                continue
            for c in commits_resp.json():
                sha = c["sha"]
                if sha not in all_commits:
                    all_commits[sha] = {
                        "sha": sha,
                        "short_sha": sha[:7],
                        "message": c["commit"]["message"].split("\n")[0],
                        "author": c["commit"]["author"]["name"],
                        "date": c["commit"]["author"]["date"],
                        "url": c["html_url"],
                        "branch": branch,
                        "parents": [p["sha"] for p in c.get("parents", [])],
                        "deployment": None,
                    }
                else:
                    # Commit exists on multiple branches — prefer main
                    if branch == "main":
                        all_commits[sha]["branch"] = branch

        # Fetch Vercel deployments
        if vercel_project and settings.VERCEL_TOKEN:
            params = {"projectId": vercel_project, "limit": 50}
            if settings.VERCEL_TEAM_ID:
                params["teamId"] = settings.VERCEL_TEAM_ID
            deploy_resp = await client.get(
                f"{VERCEL_API}/v6/deployments",
                headers={"Authorization": f"Bearer {settings.VERCEL_TOKEN}"},
                params=params,
            )
            if deploy_resp.status_code == 200:
                for d in deploy_resp.json().get("deployments", []):
                    git_sha = (d.get("meta") or {}).get("githubCommitSha", "")
                    deploy_info = {
                        "id": d.get("uid", ""),
                        "url": f"https://{d['url']}" if d.get("url") else None,
                        "state": d.get("state", ""),  # READY, ERROR, BUILDING
                        "created": d.get("created"),
                        "inspectorUrl": f"https://vercel.com/jason-clarmi/{vercel_project}/{d.get('uid', '')}",
                    }
                    if git_sha and git_sha in all_commits:
                        all_commits[git_sha]["deployment"] = deploy_info
                    elif git_sha:
                        # Commit not in our fetched history — add it
                        all_commits[git_sha] = {
                            "sha": git_sha,
                            "short_sha": git_sha[:7],
                            "message": f"Deployment {d.get('uid', '')[:8]}",
                            "author": "",
                            "date": "",
                            "url": f"https://github.com/{github_repo}/commit/{git_sha}",
                            "branch": "main",
                            "parents": [],
                            "deployment": deploy_info,
                        }

        # Count successful deployments
        deploy_count = sum(1 for c in all_commits.values() if c.get("deployment") and c["deployment"]["state"] == "READY")

        # Sort commits by date descending
        commits = sorted(all_commits.values(), key=lambda c: c.get("date", ""), reverse=True)

        return {
            "commits": commits,
            "branches": branches,
            "deploy_count": deploy_count,
        }
