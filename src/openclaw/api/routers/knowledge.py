"""Knowledge base API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from openclaw.db.deps import DBSession
from openclaw.models.knowledge import KnowledgeBase
from openclaw.api.schemas.common import PaginatedResponse
from openclaw.api.schemas.knowledge import KnowledgeRead

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("", response_model=PaginatedResponse[KnowledgeRead])
async def list_knowledge(
    session: DBSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    category: str | None = None,
    search: str | None = None,
):
    base = select(KnowledgeBase)
    if category:
        base = base.where(KnowledgeBase.category == category)
    if search:
        base = base.where(
            KnowledgeBase.title.ilike(f"%{search}%")
            | KnowledgeBase.content.ilike(f"%{search}%")
        )

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = base.order_by(KnowledgeBase.relevance_score.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    entries = result.scalars().all()

    return PaginatedResponse(
        items=[KnowledgeRead.model_validate(e) for e in entries],
        total=total,
        offset=offset,
        limit=limit,
    )
