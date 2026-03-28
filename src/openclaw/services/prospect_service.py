from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.models.prospect import Prospect


async def get_or_create_prospect(session: AsyncSession, url: str, **kwargs) -> tuple[Prospect, bool]:
    """Get existing prospect or create new one. Returns (prospect, created)."""
    stmt = select(Prospect).where(Prospect.url == url)
    result = await session.execute(stmt)
    prospect = result.scalar_one_or_none()
    if prospect:
        return prospect, False
    prospect = Prospect(url=url, **kwargs)
    session.add(prospect)
    await session.commit()
    await session.refresh(prospect)
    return prospect, True


async def get_prospect_by_url(session: AsyncSession, url: str) -> Prospect | None:
    stmt = select(Prospect).where(Prospect.url == url)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_prospects(session: AsyncSession) -> list[Prospect]:
    stmt = select(Prospect).order_by(Prospect.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())
