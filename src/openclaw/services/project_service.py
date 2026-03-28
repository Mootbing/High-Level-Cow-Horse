from __future__ import annotations

import uuid
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.models.project import Project


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
    return project


async def get_project(session: AsyncSession, project_id: str) -> Project | None:
    return await session.get(Project, project_id)


async def list_projects(session: AsyncSession, status: str | None = None) -> list[Project]:
    stmt = select(Project).order_by(Project.created_at.desc())
    if status:
        stmt = stmt.where(Project.status == status)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_project_status(session: AsyncSession, project_id: str, status: str) -> Project:
    project = await session.get(Project, project_id)
    if project:
        project.status = status
        await session.commit()
        await session.refresh(project)
    return project
