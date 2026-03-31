from __future__ import annotations

import uuid

import structlog
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.models.project import Project

logger = structlog.get_logger()


async def create_project(
    session: AsyncSession,
    name: str,
    brief: str,
    client_phone: str | None = None,
    priority: int = 5,
    prospect_id: str | None = None,
) -> Project:
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

    # -----------------------------------------------------------
    # Provision GitHub repo + Vercel project eagerly so they are
    # ready before the engineer agent starts scaffolding.
    # Failures are non-fatal — we log and continue.
    # -----------------------------------------------------------
    metadata = dict(project.metadata_ or {})

    # GitHub repo
    try:
        from openclaw.integrations.github_client import create_repo

        repo_data = await create_repo(
            name=slug,
            description=brief or f"Website for {name} — built by Clarmi Design Studio",
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
        logger.warning(
            "project_github_repo_failed",
            project_id=str(project.id),
            error=str(exc),
        )
        repo_full_name = None

    # Vercel project (only if we got a GitHub repo)
    if repo_full_name:
        try:
            from openclaw.integrations.vercel_client import create_project_from_github

            vercel_data = await create_project_from_github(slug, repo_full_name)
            metadata["vercel_project"] = vercel_data.get("name", slug)
            logger.info(
                "project_vercel_created",
                project_id=str(project.id),
                vercel_name=metadata["vercel_project"],
            )
        except Exception as exc:
            logger.warning(
                "project_vercel_failed",
                project_id=str(project.id),
                error=str(exc),
            )

    # Persist metadata back to the project row
    if metadata:
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
