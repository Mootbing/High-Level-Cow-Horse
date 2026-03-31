"""Message API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from openclaw.db.deps import DBSession
from openclaw.models.message import Message
from openclaw.api.schemas.common import PaginatedResponse
from openclaw.api.schemas.messages import MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=PaginatedResponse[MessageRead])
async def list_messages(
    session: DBSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    project_id: UUID | None = None,
):
    base = select(Message)
    if project_id:
        base = base.where(Message.project_id == project_id)

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        base.options(selectinload(Message.project))
        .order_by(Message.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages = result.scalars().all()

    items = []
    for m in messages:
        items.append(
            MessageRead(
                id=m.id,
                project_id=m.project_id,
                direction=m.direction,
                wa_message_id=m.wa_message_id,
                phone_number=m.phone_number,
                message_type=m.message_type,
                content=m.content,
                media_url=m.media_url,
                status=m.status,
                created_at=m.created_at,
                project_name=m.project.name if m.project else None,
            )
        )

    return PaginatedResponse(items=items, total=total, offset=offset, limit=limit)
