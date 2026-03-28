from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.models.task import Task


async def create_task(
    session: AsyncSession,
    project_id: str,
    agent_type: str,
    title: str,
    description: str | None = None,
    priority: int = 5,
    parent_task_id: str | None = None,
    input_data: dict | None = None,
) -> Task:
    task = Task(
        project_id=project_id,
        agent_type=agent_type,
        title=title,
        description=description,
        priority=priority,
        parent_task_id=parent_task_id,
        input_data=input_data or {},
        status="pending",
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: str) -> Task | None:
    return await session.get(Task, task_id)


async def list_tasks_for_project(session: AsyncSession, project_id: str) -> list[Task]:
    stmt = select(Task).where(Task.project_id == project_id).order_by(Task.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_task_status(
    session: AsyncSession, task_id: str, status: str,
    output_data: dict | None = None, error: str | None = None,
) -> Task | None:
    task = await session.get(Task, task_id)
    if task:
        task.status = status
        if output_data:
            task.output_data = output_data
        if error:
            task.error = error
        if status == "in_progress":
            from datetime import datetime, timezone
            task.started_at = datetime.now(timezone.utc)
        elif status in ("completed", "failed"):
            from datetime import datetime, timezone
            task.completed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(task)
    return task
