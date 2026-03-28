from __future__ import annotations

from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.models.knowledge import ImprovementMetric
from openclaw.models.task import Task
from openclaw.models.project import Project


async def get_improvement_trend(session: AsyncSession, days: int = 30) -> list[dict]:
    """Get improvement metrics over time."""
    stmt = (
        select(ImprovementMetric)
        .order_by(ImprovementMetric.metric_date.desc())
        .limit(days)
    )
    result = await session.execute(stmt)
    metrics = result.scalars().all()
    return [
        {
            "date": str(m.metric_date),
            "avg_lighthouse": m.avg_lighthouse,
            "avg_fix_loops": m.avg_fix_loops,
            "total_projects": m.total_projects,
        }
        for m in reversed(metrics)
    ]


async def compute_daily_metrics(session: AsyncSession) -> dict:
    """Compute aggregate metrics for today."""
    # Count completed projects
    projects_result = await session.execute(
        select(func.count(Project.id)).where(Project.status == "live")
    )
    total_projects = projects_result.scalar() or 0

    # Average retry count (proxy for fix loops)
    avg_retries = await session.execute(
        select(func.avg(Task.retry_count)).where(Task.status == "completed")
    )
    avg_fix_loops = avg_retries.scalar() or 0.0

    return {
        "date": str(date.today()),
        "total_projects": total_projects,
        "avg_fix_loops": round(float(avg_fix_loops), 2),
    }
