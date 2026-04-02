"""Email log API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from openclaw.db.deps import DBSession
from openclaw.models.email_log import EmailLog
from openclaw.api.schemas.common import PaginatedResponse
from openclaw.api.schemas.emails import EmailLogRead

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("", response_model=PaginatedResponse[EmailLogRead])
async def list_emails(
    session: DBSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    project_id: UUID | None = None,
    sort: str = "-created_at",
):
    base = select(EmailLog)
    if status:
        statuses = [s.strip() for s in status.split(",") if s.strip()]
        if len(statuses) == 1:
            base = base.where(EmailLog.status == statuses[0])
        elif statuses:
            base = base.where(EmailLog.status.in_(statuses))
    if project_id:
        base = base.where(EmailLog.project_id == project_id)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    desc = sort.startswith("-")
    col_name = sort.lstrip("-")
    col = getattr(EmailLog, col_name, EmailLog.created_at)
    order = col.desc() if desc else col.asc()

    stmt = (
        base.options(selectinload(EmailLog.prospect), selectinload(EmailLog.project))
        .order_by(order)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    emails = result.scalars().all()

    items = []
    for e in emails:
        items.append(
            EmailLogRead(
                id=e.id,
                prospect_id=e.prospect_id,
                project_id=e.project_id,
                to_email=e.to_email,
                subject=e.subject,
                body=e.body,
                edited_subject=e.edited_subject,
                edited_body=e.edited_body,
                status=e.status,
                gmail_message_id=e.gmail_message_id,
                created_at=e.created_at,
                sent_at=e.sent_at,
                prospect_company=e.prospect.company_name if e.prospect else None,
                project_name=e.project.name if e.project else None,
            )
        )

    return PaginatedResponse(items=items, total=total, offset=offset, limit=limit)


@router.delete("/{email_id}")
async def delete_email(session: DBSession, email_id: UUID):
    email = await session.get(EmailLog, email_id)
    if not email:
        raise HTTPException(404, "Email not found")
    if email.status == "sent":
        raise HTTPException(400, "Cannot delete a sent email")
    await session.delete(email)
    await session.commit()
    return {"ok": True}


@router.post("/{email_id}/regenerate", response_model=EmailLogRead)
async def regenerate_email(session: DBSession, email_id: UUID, body: dict | None = None):
    stmt = (
        select(EmailLog)
        .where(EmailLog.id == email_id)
        .options(selectinload(EmailLog.prospect), selectinload(EmailLog.project))
    )
    result = await session.execute(stmt)
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(404, "Email not found")
    if email.status == "sent":
        raise HTTPException(400, "Cannot regenerate a sent email")

    instructions = (body or {}).get("instructions", "")
    # Store instructions in edited_body so the agent knows what to fix
    email.edited_subject = None
    email.edited_body = f"[REGENERATE] {instructions}" if instructions else None
    email.status = "pending"
    email.created_at = func.now()
    await session.commit()
    await session.refresh(email)

    return EmailLogRead(
        id=email.id,
        prospect_id=email.prospect_id,
        project_id=email.project_id,
        to_email=email.to_email,
        subject=email.subject,
        body=email.body,
        edited_subject=email.edited_subject,
        edited_body=email.edited_body,
        status=email.status,
        gmail_message_id=email.gmail_message_id,
        created_at=email.created_at,
        sent_at=email.sent_at,
        prospect_company=email.prospect.company_name if email.prospect else None,
        project_name=email.project.name if email.project else None,
    )


@router.get("/{email_id}", response_model=EmailLogRead)
async def get_email(session: DBSession, email_id: UUID):
    stmt = (
        select(EmailLog)
        .where(EmailLog.id == email_id)
        .options(selectinload(EmailLog.prospect), selectinload(EmailLog.project))
    )
    result = await session.execute(stmt)
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(404, "Email not found")

    return EmailLogRead(
        id=email.id,
        prospect_id=email.prospect_id,
        project_id=email.project_id,
        to_email=email.to_email,
        subject=email.subject,
        body=email.body,
        edited_subject=email.edited_subject,
        edited_body=email.edited_body,
        status=email.status,
        gmail_message_id=email.gmail_message_id,
        created_at=email.created_at,
        sent_at=email.sent_at,
        prospect_company=email.prospect.company_name if email.prospect else None,
        project_name=email.project.name if email.project else None,
    )
