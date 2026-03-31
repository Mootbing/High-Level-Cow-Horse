"""Task API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from openclaw.db.deps import DBSession
from openclaw.models.task import Task
from openclaw.models.project import Project
from openclaw.api.schemas.common import PaginatedResponse
from openclaw.api.schemas.tasks import TaskRead

router = APIRouter(tags=["tasks"])


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
async def list_project_tasks(session: DBSession, project_id: UUID):
    stmt = select(Task).where(Task.project_id == project_id).order_by(Task.created_at)
    result = await session.execute(stmt)
    tasks = result.scalars().all()
    return [TaskRead.model_validate(t) for t in tasks]


@router.get("/tasks", response_model=PaginatedResponse[TaskRead])
async def list_tasks(
    session: DBSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    agent_type: str | None = None,
):
    base = select(Task)
    if status:
        base = base.where(Task.status == status)
    if agent_type:
        base = base.where(Task.agent_type == agent_type)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = base.order_by(Task.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    tasks = result.scalars().all()

    return PaginatedResponse(
        items=[TaskRead.model_validate(t) for t in tasks],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(session: DBSession, task_id: UUID):
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return TaskRead.model_validate(task)
