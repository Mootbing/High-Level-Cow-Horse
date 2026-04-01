from __future__ import annotations

import uuid

import structlog
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.models.project import Project

logger = structlog.get_logger()


async def find_project_by_name(session: AsyncSession, name: str) -> Project | None:
    """Find a project by name — single source of truth for project lookup.

    Strategy (in order):
    1. Exact name match (case-insensitive)
    2. Slug prefix match (for when callers pass the slug base)
    If multiple matches, return the most recently created one.
    """
    # 1. Exact name match (case-insensitive)
    stmt = (
        select(Project)
        .where(Project.name.ilike(name))
        .order_by(Project.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    project = result.scalars().first()
    if project:
        return project

    # 2. Slug prefix match (the slugified name is the prefix before the hash)
    slug_prefix = slugify(name)
    stmt = (
        select(Project)
        .where(Project.slug.startswith(slug_prefix))
        .order_by(Project.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_project(
    session: AsyncSession,
    name: str,
    brief: str,
    client_phone: str | None = None,
    priority: int = 5,
    prospect_id: str | None = None,
) -> Project:
    # --- Dedup check: return existing project if one with same name exists ---
    existing = await find_project_by_name(session, name)
    if existing:
        logger.info(
            "project_already_exists",
            project_id=str(existing.id),
            slug=existing.slug,
            name=existing.name,
        )
        # If existing project is missing GitHub/Vercel, try to provision now
        metadata = dict(existing.metadata_ or {})
        if not metadata.get("github_repo") or not metadata.get("vercel_project"):
            existing = await _provision_github_vercel(session, existing)
        return existing

    slug = slugify(name) + "-" + uuid.uuid4().hex[:6]
    project = Project(
        name=name,
        slug=slug,
        brief=brief,
        client_phone=client_phone,
        priority=priority,
        prospect_id=prospect_id,
        status="intake",
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)

    # Provision GitHub + Vercel — CRITICAL, error out if they fail
    project = await _provision_github_vercel(session, project)
    return project


async def _provision_github_vercel(
    session: AsyncSession, project: Project
) -> Project:
    """Provision GitHub repo + Vercel project. Raises on failure."""
    from openclaw.integrations.github_client import create_repo, get_repo

    metadata = dict(project.metadata_ or {})

    # GitHub repo — verify it actually exists if metadata claims it does
    needs_repo = True
    if metadata.get("github_repo"):
        try:
            await get_repo(metadata["github_repo"])
            needs_repo = False  # repo exists, keep it
            repo_full_name = metadata["github_repo"]
        except Exception:
            # Repo in metadata doesn't actually exist — clear stale data
            logger.warning(
                "stale_github_repo_cleared",
                project_id=str(project.id),
                stale_repo=metadata["github_repo"],
            )
            metadata.pop("github_repo", None)
            metadata.pop("github_url", None)

    if needs_repo:
        try:
            repo_data = await create_repo(
                name=project.slug,
                description=project.brief or f"Website for {project.name} — built by Clarmi Design Studio",
            )
            repo_full_name = repo_data["full_name"]
            metadata["github_repo"] = repo_full_name
            metadata["github_url"] = f"https://github.com/{repo_full_name}"
            logger.info(
                "project_github_repo_created",
                project_id=str(project.id),
                repo=repo_full_name,
            )
        except Exception as exc:
            logger.error(
                "project_github_repo_failed",
                project_id=str(project.id),
                error=str(exc),
            )
            raise RuntimeError(
                f"CRITICAL: Failed to create GitHub repo for '{project.name}': {exc}"
            ) from exc
    else:
        repo_full_name = metadata["github_repo"]

    # Vercel project — verify it exists if metadata claims it does
    from openclaw.integrations.vercel_client import create_project_from_github

    needs_vercel = True
    if metadata.get("vercel_project"):
        try:
            from openclaw.integrations.vercel_client import get_latest_deployment
            # If we can query the project at all, it exists (even with no deployments)
            await get_latest_deployment(metadata["vercel_project"])
            needs_vercel = False
        except Exception:
            logger.warning(
                "stale_vercel_project_cleared",
                project_id=str(project.id),
                stale_vercel=metadata["vercel_project"],
            )
            metadata.pop("vercel_project", None)

    if needs_vercel:
        try:
            vercel_data = await create_project_from_github(project.slug, repo_full_name)
            metadata["vercel_project"] = vercel_data.get("name", project.slug)
            logger.info(
                "project_vercel_created",
                project_id=str(project.id),
                vercel_name=metadata["vercel_project"],
            )
        except Exception as exc:
            logger.error(
                "project_vercel_failed",
                project_id=str(project.id),
                error=str(exc),
            )
            raise RuntimeError(
                f"CRITICAL: Failed to create Vercel project for '{project.name}': {exc}"
            ) from exc

    # Persist metadata
    project.metadata_ = metadata
    await session.commit()
    await session.refresh(project)
    return project


async def get_project(session: AsyncSession, project_id: str) -> Project | None:
    pid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
    return await session.get(Project, pid)


async def list_projects(session: AsyncSession, status: str | None = None) -> list[Project]:
    stmt = select(Project).order_by(Project.created_at.desc())
    if status:
        stmt = stmt.where(Project.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_project_status(session: AsyncSession, project_id: str, status: str) -> Project:
    pid = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
    project = await session.get(Project, pid)
    if project:
        project.status = status
        await session.commit()
        await session.refresh(project)
    return project
