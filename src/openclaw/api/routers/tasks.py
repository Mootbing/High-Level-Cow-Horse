"""Task API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

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
    sort: str = "-created_at",
):
    base = select(Task)
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if len(statuses) == 1:
            base = base.where(Task.status == statuses[0])
        elif statuses:
            base = base.where(Task.status.in_(statuses))
    if agent_type:
        base = base.where(Task.agent_type == agent_type)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    desc = sort.startswith("-")
    col_name = sort.lstrip("-")
    col = getattr(Task, col_name, Task.created_at)
    order = col.desc() if desc else col.asc()

    stmt = (
        base.options(selectinload(Task.project))
        .order_by(order)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    tasks = result.scalars().all()

    items = []
    for t in tasks:
        read = TaskRead.model_validate(t)
        read.project_name = t.project.name if t.project else None
        items.append(read)

    return PaginatedResponse(
        items=items,
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


@router.post("/tasks/{task_id}/retry", response_model=TaskRead)
async def retry_task(session: DBSession, task_id: UUID):
    stmt = (
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.project))
    )
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status not in ("failed", "completed"):
        raise HTTPException(400, f"Cannot retry task with status '{task.status}'")

    task.status = "pending"
    task.error = None
    task.retry_count = 0
    task.started_at = None
    task.completed_at = None
    task.output_data = {}
    await session.commit()
    await session.refresh(task)

    read = TaskRead.model_validate(task)
    read.project_name = task.project.name if task.project else None
    return read
