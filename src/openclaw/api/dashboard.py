"""Dashboard REST API endpoints."""

from __future__ import annotations

import datetime

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from openclaw.api.auth import verify_dashboard_token
from openclaw.config import settings
from openclaw.db.session import get_session
from openclaw.models.agent_log import AgentLog
from openclaw.models.email_log import EmailLog
from openclaw.models.knowledge import KnowledgeBase
from openclaw.models.message import Message
from openclaw.models.project import Project
from openclaw.models.prospect import Prospect
from openclaw.models.task import Task
from openclaw.queue.streams import AGENT_TYPES, LIGHT_AGENTS, HEAVY_AGENTS, stream_name, group_name
from openclaw.schemas.dashboard import (
    AgentLogSummary,
    AgentsStatusResponse,
    AgentStatus,
    EmailDraftResponse,
    EmailDraftUpdate,
    EmailLogSummary,
    KanbanBoardResponse,
    KanbanColumn,
    KanbanTaskCard,
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
    # Single query with aggregated task counts (avoids N+1)
    task_total = (
        select(Task.project_id, func.count().label("total"))
        .group_by(Task.project_id)
        .subquery()
    )
    task_done = (
        select(Task.project_id, func.count().label("done"))
        .where(Task.status == "completed")
        .group_by(Task.project_id)
        .subquery()
    )

    q = (
        select(
            Project,
            func.coalesce(task_total.c.total, 0).label("task_count"),
            func.coalesce(task_done.c.done, 0).label("completed_task_count"),
        )
        .outerjoin(task_total, Project.id == task_total.c.project_id)
        .outerjoin(task_done, Project.id == task_done.c.project_id)
        .order_by(Project.created_at.desc())
    )
    if status:
        q = q.where(Project.status == status)

    result = await session.execute(q)
    rows = result.all()

    return [
        ProjectSummary(
            id=row.Project.id,
            name=row.Project.name,
            slug=row.Project.slug,
            status=row.Project.status,
            priority=row.Project.priority,
            deployed_url=row.Project.deployed_url,
            task_count=row.task_count,
            completed_task_count=row.completed_task_count,
            created_at=row.Project.created_at,
            updated_at=row.Project.updated_at,
        )
        for row in rows
    ]


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


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    """Delete a project and clean up GitHub repo + Vercel project."""
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    slug = project.slug

    # Clean up GitHub repo
    try:
        from openclaw.integrations.github_client import get_authenticated_user, delete_repo
        user = await get_authenticated_user()
        await delete_repo(f"{user}/{slug}")
    except Exception:
        pass  # Best-effort

    # Clean up Vercel project
    try:
        from openclaw.integrations.vercel_client import delete_project as vercel_delete
        await vercel_delete(slug)
    except Exception:
        pass  # Best-effort

    # Delete from DB (cascades to tasks, assets, deployments)
    await session.delete(project)
    await session.commit()

    return {"status": "deleted", "slug": slug}


# --- Kanban Board ---

KANBAN_COLUMNS = [
    ("pending", "Queued"),
    ("in_progress", "In Progress"),
    ("review", "Review"),
    ("completed", "Done"),
    ("failed", "Failed"),
]


async def _build_kanban_board(session: AsyncSession, project_id: str | None = None) -> KanbanBoardResponse:
    base_q = (
        select(Task, Project.name.label("project_name"))
        .outerjoin(Project, Task.project_id == Project.id)
        .order_by(Task.priority.asc(), Task.created_at.desc())
    )
    if project_id:
        base_q = base_q.where(Task.project_id == project_id)

    result = await session.execute(base_q)
    rows = result.all()

    columns = []
    total = 0
    for status, label in KANBAN_COLUMNS:
        cards = []
        for row in rows:
            task = row.Task
            if task.status != status:
                continue
            delegated_by = task.input_data.get("source_agent") if task.input_data else None
            cards.append(KanbanTaskCard(
                id=task.id,
                project_id=task.project_id,
                project_name=row.project_name,
                agent_type=task.agent_type,
                title=task.title,
                status=task.status,
                priority=task.priority,
                delegated_by=delegated_by,
                started_at=task.started_at,
                completed_at=task.completed_at,
                created_at=task.created_at,
                error=task.error,
                latest_log_id=None,
            ))
        total += len(cards)
        columns.append(KanbanColumn(status=status, label=label, cards=cards, count=len(cards)))

    return KanbanBoardResponse(columns=columns, total_tasks=total)


@router.get("/kanban/global", response_model=KanbanBoardResponse)
async def kanban_global(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    return await _build_kanban_board(session)


@router.get("/kanban/project/{project_id}", response_model=KanbanBoardResponse)
async def kanban_project(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    return await _build_kanban_board(session, project_id=project_id)


# --- Agents Status ---

@router.get("/agents/status", response_model=AgentsStatusResponse)
async def agents_status(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)

    # Fetch current in-progress tasks per agent type
    result = await session.execute(
        select(Task.agent_type, Task.title)
        .where(Task.status == "in_progress")
        .order_by(Task.started_at.desc())
    )
    current_tasks: dict[str, str] = {}
    for row in result.all():
        if row.agent_type not in current_tasks:
            current_tasks[row.agent_type] = row.title

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
            current_task=current_tasks.get(agent_type),
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
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    q = select(EmailLog).order_by(EmailLog.created_at.desc()).limit(limit)
    if status:
        q = q.where(EmailLog.status == status)
    result = await session.execute(q)
    return [EmailLogSummary.model_validate(e) for e in result.scalars().all()]


@router.get("/emails/drafts", response_model=list[EmailLogSummary])
async def list_email_drafts(
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    """List all emails with status='draft', newest first."""
    result = await session.execute(
        select(EmailLog)
        .where(EmailLog.status == "draft")
        .order_by(EmailLog.created_at.desc())
    )
    return [EmailLogSummary.model_validate(e) for e in result.scalars().all()]


@router.put("/emails/{email_id}", response_model=EmailDraftResponse)
async def update_email_draft(
    email_id: str,
    payload: EmailDraftUpdate,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    """Update the subject and/or body of a draft email."""
    result = await session.execute(
        select(EmailLog).where(EmailLog.id == email_id)
    )
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    if email.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft emails can be edited")

    if payload.subject is not None:
        email.edited_subject = payload.subject
    if payload.body is not None:
        email.edited_body = payload.body

    await session.commit()
    await session.refresh(email)
    return EmailDraftResponse.model_validate(email)


@router.post("/emails/{email_id}/send", response_model=EmailDraftResponse)
async def send_email_draft(
    email_id: str,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    """Approve and send a draft email via Gmail."""
    from openclaw.integrations.gmail_client import send_email

    result = await session.execute(
        select(EmailLog).where(EmailLog.id == email_id)
    )
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    if email.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft emails can be sent")

    # Use edited fields if present, otherwise fall back to originals
    subject = email.edited_subject or email.subject
    body = email.edited_body or email.body

    gmail_result = await send_email(
        to=email.to_email,
        subject=subject or "",
        body=body or "",
    )

    email.status = "sent"
    email.gmail_message_id = gmail_result.get("id", "")
    email.sent_at = datetime.datetime.now(datetime.timezone.utc)
    await session.commit()
    await session.refresh(email)
    return EmailDraftResponse.model_validate(email)


@router.delete("/emails/{email_id}")
async def discard_email_draft(
    email_id: str,
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    """Discard (delete) a draft email."""
    result = await session.execute(
        select(EmailLog).where(EmailLog.id == email_id)
    )
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    if email.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft emails can be discarded")

    await session.delete(email)
    await session.commit()
    return {"status": "discarded", "id": email_id}


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


# --- Agent Logs ---

@router.get("/agent-logs", response_model=list[AgentLogSummary])
async def list_agent_logs(
    agent_type: str | None = None,
    project_id: str | None = None,
    limit: int = Query(100, le=500),
    session: AsyncSession = Depends(get_session),
    _: str = Depends(verify_dashboard_token),
):
    """List agent logs, optionally filtered by agent type and/or project."""
    q = select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
    if agent_type:
        q = q.where(AgentLog.agent_type == agent_type)
    if project_id:
        q = q.where(AgentLog.project_id == project_id)
    result = await session.execute(q)
    return [AgentLogSummary.model_validate(a) for a in result.scalars().all()]


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


# --- Queue Management ---

@router.get("/queues")
async def get_queues(
    _: str = Depends(verify_dashboard_token),
):
    """Get queue depths and pending messages for all agents."""
    from openclaw.queue.streams import AGENT_TYPES, stream_name, group_name

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        queues = []
        for agent_type in AGENT_TYPES:
            stream = stream_name(agent_type)
            group = group_name(agent_type)
            try:
                # Get stream length
                length = await r.xlen(stream)

                # Get pending messages
                pending = 0
                try:
                    info = await r.xpending(stream, group)
                    pending = info.get("pending", 0) if isinstance(info, dict) else (info[0] if info else 0)
                except Exception:
                    pass

                # Get last 10 messages for preview
                messages = []
                try:
                    entries = await r.xrevrange(stream, count=10)
                    import json as _json
                    for entry_id, fields in entries:
                        try:
                            data = _json.loads(fields.get("data", "{}"))
                            messages.append({
                                "entry_id": entry_id,
                                "type": data.get("type", "?"),
                                "source": data.get("source_agent", "?"),
                                "target": data.get("target_agent", agent_type),
                                "task_id": data.get("task_id"),
                                "preview": str(data.get("payload", {}).get("prompt", ""))[:150],
                                "timestamp": fields.get("timestamp"),
                            })
                        except Exception:
                            messages.append({"entry_id": entry_id, "raw": str(fields)[:150]})
                except Exception:
                    pass

                queues.append({
                    "agent_type": agent_type,
                    "stream_length": length,
                    "pending": pending,
                    "messages": messages,
                })
            except Exception as e:
                queues.append({"agent_type": agent_type, "error": str(e)[:200]})
        return queues
    finally:
        await r.aclose()


@router.delete("/queues/{agent_type}")
async def flush_queue(
    agent_type: str,
    _: str = Depends(verify_dashboard_token),
):
    """Flush all messages from an agent's queue."""
    from openclaw.queue.streams import AGENT_TYPES, stream_name, group_name

    if agent_type != "all" and agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        flushed = []
        targets = AGENT_TYPES if agent_type == "all" else [agent_type]
        for at in targets:
            stream = stream_name(at)
            try:
                length = await r.xlen(stream)
                await r.delete(stream)
                # Recreate stream and consumer group
                group = group_name(at)
                try:
                    await r.xgroup_create(stream, group, id="0", mkstream=True)
                except redis.ResponseError:
                    pass
                flushed.append({"agent_type": at, "messages_flushed": length})
            except Exception as e:
                flushed.append({"agent_type": at, "error": str(e)[:200]})

        # Also flush dedup keys
        dedup_keys = []
        async for key in r.scan_iter("openclaw:dedup:*"):
            dedup_keys.append(key)
        if dedup_keys:
            await r.delete(*dedup_keys)

        return {"status": "flushed", "details": flushed, "dedup_keys_cleared": len(dedup_keys)}
    finally:
        await r.aclose()


@router.delete("/queues/{agent_type}/{entry_id}")
async def cancel_message(
    agent_type: str,
    entry_id: str,
    _: str = Depends(verify_dashboard_token),
):
    """Delete a specific message from an agent's queue."""
    from openclaw.queue.streams import AGENT_TYPES, stream_name

    if agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")

    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        stream = stream_name(agent_type)
        deleted = await r.xdel(stream, entry_id)
        return {"status": "cancelled" if deleted else "not_found", "entry_id": entry_id, "agent_type": agent_type}
    finally:
        await r.aclose()
