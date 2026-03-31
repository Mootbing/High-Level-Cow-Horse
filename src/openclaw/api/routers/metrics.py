"""Metrics and dashboard stats API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from openclaw.db.deps import DBSession
from openclaw.models.project import Project
from openclaw.models.prospect import Prospect
from openclaw.models.email_log import EmailLog
from openclaw.models.task import Task
from openclaw.models.knowledge import ImprovementMetric
from openclaw.api.schemas.metrics import DashboardStats, MetricRead

router = APIRouter(prefix="/metrics", tags=["metrics"])

STATUSES = ["intake", "pitch", "design", "build", "qa", "deployed"]


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(session: DBSession):
    total_prospects = (await session.execute(select(func.count(Prospect.id)))).scalar() or 0
    total_projects = (await session.execute(select(func.count(Project.id)))).scalar() or 0

    active_q = select(func.count(Project.id)).where(Project.status.notin_(["deployed"]))
    active_projects = (await session.execute(active_q)).scalar() or 0

    deployed_q = select(func.count(Project.id)).where(Project.status == "deployed")
    deployed_projects = (await session.execute(deployed_q)).scalar() or 0

    emails_sent = (
        await session.execute(select(func.count(EmailLog.id)).where(EmailLog.status == "sent"))
    ).scalar() or 0

    emails_draft = (
        await session.execute(select(func.count(EmailLog.id)).where(EmailLog.status == "draft"))
    ).scalar() or 0

    tasks_in_progress = (
        await session.execute(select(func.count(Task.id)).where(Task.status == "in_progress"))
    ).scalar() or 0

    tasks_completed = (
        await session.execute(select(func.count(Task.id)).where(Task.status == "completed"))
    ).scalar() or 0

    # Latest lighthouse
    latest_metric = await session.execute(
        select(ImprovementMetric).order_by(ImprovementMetric.metric_date.desc()).limit(1)
    )
    metric = latest_metric.scalar_one_or_none()
    avg_lighthouse = metric.avg_lighthouse if metric else None

    # Projects by status
    projects_by_status: dict[str, int] = {}
    for s in STATUSES:
        cnt = (
            await session.execute(select(func.count(Project.id)).where(Project.status == s))
        ).scalar() or 0
        projects_by_status[s] = cnt

    return DashboardStats(
        total_prospects=total_prospects,
        total_projects=total_projects,
        active_projects=active_projects,
        deployed_projects=deployed_projects,
        emails_sent=emails_sent,
        emails_draft=emails_draft,
        tasks_in_progress=tasks_in_progress,
        tasks_completed=tasks_completed,
        avg_lighthouse=avg_lighthouse,
        projects_by_status=projects_by_status,
    )


@router.get("", response_model=list[MetricRead])
async def list_metrics(session: DBSession, days: int = Query(30, ge=1, le=365)):
    stmt = (
        select(ImprovementMetric)
        .order_by(ImprovementMetric.metric_date.desc())
        .limit(days)
    )
    result = await session.execute(stmt)
    metrics = result.scalars().all()
    return [MetricRead.model_validate(m) for m in reversed(list(metrics))]
