from __future__ import annotations

import math
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.models.knowledge import KnowledgeBase, PromptVersion


async def search_knowledge(
    session: AsyncSession,
    category: str | None = None,
    tags: list[str] | None = None,
    min_relevance: float = 0.3,
    limit: int = 20,
) -> list[KnowledgeBase]:
    """Search knowledge base with optional filters."""
    stmt = select(KnowledgeBase).where(
        KnowledgeBase.relevance_score >= min_relevance
    ).order_by(KnowledgeBase.relevance_score.desc()).limit(limit)

    if category:
        stmt = stmt.where(KnowledgeBase.category == category)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def decay_relevance(session: AsyncSession, halflife_days: int = 90) -> int:
    """Apply exponential decay to knowledge entry relevance scores.
    Returns number of entries updated.
    """
    entries = await session.execute(select(KnowledgeBase))
    count = 0
    now = datetime.now(timezone.utc)
    for entry in entries.scalars().all():
        if entry.category == "learning":
            continue  # Learnings never decay
        age_days = (now - entry.created_at.replace(tzinfo=timezone.utc)).days
        decay_factor = math.pow(0.5, age_days / halflife_days)
        new_score = max(0.01, decay_factor)
        if abs(entry.relevance_score - new_score) > 0.01:
            entry.relevance_score = new_score
            count += 1
    await session.commit()
    return count


async def get_latest_prompt(session: AsyncSession, template_name: str) -> PromptVersion | None:
    """Get the latest version of a prompt template."""
    stmt = (
        select(PromptVersion)
        .where(PromptVersion.template_name == template_name)
        .order_by(PromptVersion.version.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
