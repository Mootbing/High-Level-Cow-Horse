"""Learning tools — analyze completed projects and track improvement metrics."""

import json
from datetime import date

from openclaw.mcp_server.server import mcp


@mcp.tool()
async def analyze_project(project_id: str) -> str:
    """Analyze a completed project — returns task history, timings, and success/failure data for learning."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.project import Project
    from openclaw.models.task import Task
    from sqlalchemy import select

    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if not project:
            return json.dumps({"error": f"Project {project_id} not found"})

        stmt = select(Task).where(Task.project_id == project.id).order_by(Task.created_at)
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        task_data = []
        for t in tasks:
            task_data.append({
                "agent_type": t.agent_type,
                "title": t.title,
                "status": t.status,
                "retry_count": t.retry_count,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "error": t.error[:200] if t.error else None,
            })

        return json.dumps({
            "project": {
                "name": project.name,
                "status": project.status,
                "deployed_url": project.deployed_url,
                "created": project.created_at.isoformat() if project.created_at else None,
            },
            "tasks": task_data,
            "total_tasks": len(tasks),
            "failed_tasks": sum(1 for t in tasks if t.status == "failed"),
            "total_retries": sum(t.retry_count or 0 for t in tasks),
        }, indent=2)


@mcp.tool()
async def log_metrics(
    avg_lighthouse: float | None = None,
    avg_fix_loops: float | None = None,
    total_projects: int | None = None,
    notes: str | None = None,
) -> str:
    """Log daily improvement metrics — Lighthouse scores, fix loop counts, project totals."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.knowledge import ImprovementMetric

    async with async_session_factory() as session:
        metric = ImprovementMetric(
            metric_date=date.today(),
            avg_lighthouse=avg_lighthouse,
            avg_fix_loops=avg_fix_loops,
            total_projects=total_projects,
            notes=notes,
        )
        session.add(metric)
        await session.commit()
        await session.refresh(metric)

        return json.dumps({
            "metric_id": str(metric.id),
            "date": str(metric.metric_date),
            "status": "logged",
        })
