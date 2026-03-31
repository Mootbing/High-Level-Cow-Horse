"""Project API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from openclaw.db.deps import DBSession
from openclaw.models.project import Project
from openclaw.models.prospect import Prospect
from openclaw.models.task import Task
from openclaw.models.asset import Asset
from openclaw.api.schemas.common import PaginatedResponse
from openclaw.api.schemas.projects import ProjectRead, ProjectStats, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

STATUSES = ["intake", "pitch", "design", "build", "qa", "deployed"]


@router.get("/stats", response_model=ProjectStats)
async def get_project_stats(session: DBSession):
    total_q = await session.execute(select(func.count(Project.id)))
    total = total_q.scalar() or 0

    by_status: dict[str, int] = {}
    for status in STATUSES:
        cnt = await session.execute(
            select(func.count(Project.id)).where(Project.status == status)
        )
        by_status[status] = cnt.scalar() or 0

    return ProjectStats(total=total, by_status=by_status)


@router.get("", response_model=PaginatedResponse[ProjectRead])
async def list_projects(
    session: DBSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    search: str | None = None,
    sort: str = "-created_at",
):
    base = select(Project)
    if status:
        base = base.where(Project.status == status)
    if search:
        base = base.where(
            Project.name.ilike(f"%{search}%") | Project.slug.ilike(f"%{search}%")
        )

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    desc = sort.startswith("-")
    col_name = sort.lstrip("-")
    col = getattr(Project, col_name, Project.created_at)
    order = col.desc() if desc else col.asc()

    stmt = (
        base.options(
            selectinload(Project.prospect),
            selectinload(Project.tasks),
            selectinload(Project.assets),
        )
        .order_by(order)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    projects = result.scalars().all()

    items = []
    for p in projects:
        items.append(
            ProjectRead(
                id=p.id,
                name=p.name,
                slug=p.slug,
                client_phone=p.client_phone,
                brief=p.brief,
                status=p.status,
                priority=p.priority,
                prospect_id=p.prospect_id,
                metadata_=p.metadata_ or {},
                deployed_url=p.deployed_url,
                created_at=p.created_at,
                updated_at=p.updated_at,
                prospect_company=p.prospect.company_name if p.prospect else None,
                task_count=len(p.tasks),
                asset_count=len(p.assets),
            )
        )

    return PaginatedResponse(items=items, total=total, offset=offset, limit=limit)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(session: DBSession, project_id: UUID):
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.prospect),
            selectinload(Project.tasks),
            selectinload(Project.assets),
        )
    )
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")

    return ProjectRead(
        id=project.id,
        name=project.name,
        slug=project.slug,
        client_phone=project.client_phone,
        brief=project.brief,
        status=project.status,
        priority=project.priority,
        prospect_id=project.prospect_id,
        metadata_=project.metadata_ or {},
        deployed_url=project.deployed_url,
        created_at=project.created_at,
        updated_at=project.updated_at,
        prospect_company=project.prospect.company_name if project.prospect else None,
        task_count=len(project.tasks),
        asset_count=len(project.assets),
    )


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(session: DBSession, project_id: UUID, data: ProjectUpdate):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await session.commit()
    await session.refresh(project)
    return ProjectRead.model_validate(project)
