"""Dashboard REST API endpoints."""

from __future__ import annotations

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from openclaw.api.auth import verify_dashboard_token
from openclaw.config import settings
from openclaw.db.session import get_session
from openclaw.models.email_log import EmailLog
from openclaw.models.knowledge import KnowledgeBase
from openclaw.models.message import Message
from openclaw.models.project import Project
from openclaw.models.prospect import Prospect
from openclaw.models.task import Task
from openclaw.queue.streams import AGENT_TYPES, LIGHT_AGENTS, HEAVY_AGENTS, stream_name, group_name
from openclaw.schemas.dashboard import (
    AgentsStatusResponse,
    AgentStatus,
    EmailLogSummary,
    KnowledgeEntrySummary,
    MessageSummary,
    OverviewResponse,
    ProjectDetail,
    ProjectSummary,
    ProspectSummary,
    TaskSummary,
)

router = APIRouter()


# --- Overview ---

@router.get("/overview", response_model=OverviewResponse)
async def overview(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    active = await session.scalar(
        select(func.count()).select_from(Project).where(Project.status.notin_(["deployed", "cancelled"]))
    )
    total = await session.scalar(select(func.count()).select_from(Project))
    pending_tasks = await session.scalar(
        select(func.count()).select_from(Task).where(Task.status == "pending")
    )
    completed_tasks = await session.scalar(
        select(func.count()).select_from(Task).where(Task.status == "completed")
    )
    prospects = await session.scalar(select(func.count()).select_from(Prospect))
    emails = await session.scalar(select(func.count()).select_from(EmailLog))
    knowledge = await session.scalar(select(func.count()).select_from(KnowledgeBase))

    return OverviewResponse(
        active_projects=active or 0,
        total_projects=total or 0,
        pending_tasks=pending_tasks or 0,
        completed_tasks=completed_tasks or 0,
        total_prospects=prospects or 0,
        total_emails_sent=emails or 0,
        knowledge_entries=knowledge or 0,
    )


# --- Projects ---

@router.get("/projects", response_model=list[ProjectSummary])
async def list_projects(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    q = select(Project).order_by(Project.created_at.desc())
    if status:
        q = q.where(Project.status == status)

    result = await session.execute(q)
    projects = result.scalars().all()

    summaries = []
    for p in projects:
        task_count = await session.scalar(
            select(func.count()).select_from(Task).where(Task.project_id == p.id)
        )
        completed = await session.scalar(
            select(func.count()).select_from(Task).where(
                Task.project_id == p.id, Task.status == "completed"
            )
        )
        summaries.append(ProjectSummary(
            id=p.id,
            name=p.name,
            slug=p.slug,
            status=p.status,
            priority=p.priority,
            deployed_url=p.deployed_url,
            task_count=task_count or 0,
            completed_task_count=completed or 0,
            created_at=p.created_at,
            updated_at=p.updated_at,
        ))
    return summaries


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    result = await session.execute(
        select(Project).where(Project.id == project_id).options(
            selectinload(Project.tasks)
        )
    )
    project = result.scalar_one_or_none()
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectDetail(
        id=project.id,
        name=project.name,
        slug=project.slug,
        brief=project.brief,
        status=project.status,
        priority=project.priority,
        deployed_url=project.deployed_url,
        metadata_=project.metadata_,
        created_at=project.created_at,
        updated_at=project.updated_at,
        tasks=[TaskSummary(
            id=t.id,
            agent_type=t.agent_type,
            title=t.title,
            status=t.status,
            priority=t.priority,
            parent_task_id=t.parent_task_id,
            started_at=t.started_at,
            completed_at=t.completed_at,
            created_at=t.created_at,
        ) for t in project.tasks],
    )


# --- Agents Status ---

@router.get("/agents/status", response_model=AgentsStatusResponse)
async def agents_status(
    _: str = Depends(verify_dashboard_token),
):
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    agents = []
    total_pending = 0

    for agent_type in AGENT_TYPES:
        tier = "light" if agent_type in LIGHT_AGENTS else "heavy"

        # Check heartbeat
        hb_keys = await r.keys(f"health:{agent_type}:*")
        status = "alive" if hb_keys else "dead"
        last_hb = None
        if hb_keys:
            last_hb = await r.get(hb_keys[0])

        # Check queue depth
        depth = 0
        try:
            groups = await r.xinfo_groups(stream_name(agent_type))
            for g in groups:
                depth += g.get("lag", 0) or g.get("pending", 0)
        except Exception:
            pass

        total_pending += depth
        agents.append(AgentStatus(
            agent_type=agent_type,
            tier=tier,
            status=status,
            queue_depth=depth,
            last_heartbeat=last_hb,
        ))

    await r.aclose()
    return AgentsStatusResponse(agents=agents, total_pending=total_pending)


# --- Prospects ---

@router.get("/prospects", response_model=list[ProspectSummary])
async def list_prospects(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    result = await session.execute(
        select(Prospect).order_by(Prospect.created_at.desc()).limit(100)
    )
    return [ProspectSummary.model_validate(p) for p in result.scalars().all()]


# --- Emails ---

@router.get("/emails", response_model=list[EmailLogSummary])
async def list_emails(
    limit: int = Query(50, le=200),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    result = await session.execute(
        select(EmailLog).order_by(EmailLog.sent_at.desc()).limit(limit)
    )
    return [EmailLogSummary.model_validate(e) for e in result.scalars().all()]


# --- Knowledge ---

@router.get("/knowledge", response_model=list[KnowledgeEntrySummary])
async def list_knowledge(
    category: str | None = None,
    limit: int = Query(50, le=200),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    q = select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).limit(limit)
    if category:
        q = q.where(KnowledgeBase.category == category)
    result = await session.execute(q)
    return [KnowledgeEntrySummary.model_validate(k) for k in result.scalars().all()]


# --- Chat History ---

@router.get("/messages", response_model=list[MessageSummary])
async def list_messages(
    limit: int = Query(50, le=200),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    result = await session.execute(
        select(Message)
        .where(Message.phone_number == "dashboard")
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return [MessageSummary.model_validate(m) for m in result.scalars().all()]
