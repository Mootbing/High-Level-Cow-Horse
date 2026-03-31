"""Prospect API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from openclaw.db.deps import DBSession
from openclaw.models.prospect import Prospect
from openclaw.models.project import Project
from openclaw.api.schemas.common import PaginatedResponse
from openclaw.api.schemas.prospects import ProspectGeo, ProspectRead, ProspectUpdate

router = APIRouter(prefix="/prospects", tags=["prospects"])


@router.get("", response_model=PaginatedResponse[ProspectRead])
async def list_prospects(
    session: DBSession,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    industry: str | None = None,
    search: str | None = None,
    sort: str = "-created_at",
):
    base = select(Prospect)
    if industry:
        base = base.where(Prospect.industry == industry)
    if search:
        base = base.where(
            Prospect.company_name.ilike(f"%{search}%")
            | Prospect.url.ilike(f"%{search}%")
            | Prospect.industry.ilike(f"%{search}%")
        )

    # Count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # Sort
    desc = sort.startswith("-")
    col_name = sort.lstrip("-")
    col = getattr(Prospect, col_name, Prospect.created_at)
    order = col.desc() if desc else col.asc()

    stmt = base.options(selectinload(Prospect.projects)).order_by(order).offset(offset).limit(limit)
    result = await session.execute(stmt)
    prospects = result.scalars().all()

    items = []
    for p in prospects:
        problems = p.raw_data.get("site_problems", []) if p.raw_data else []
        items.append(
            ProspectRead(
                id=p.id,
                url=p.url,
                company_name=p.company_name,
                tagline=p.tagline,
                contact_emails=p.contact_emails or [],
                brand_colors=p.brand_colors or [],
                fonts=p.fonts or [],
                logo_url=p.logo_url,
                social_links=p.social_links or {},
                industry=p.industry,
                tech_stack=p.tech_stack or [],
                raw_data=p.raw_data or {},
                latitude=p.latitude,
                longitude=p.longitude,
                scraped_at=p.scraped_at,
                created_at=p.created_at,
                project_count=len(p.projects),
                site_problems_count=len(problems),
            )
        )

    return PaginatedResponse(items=items, total=total, offset=offset, limit=limit)


@router.get("/geo", response_model=list[ProspectGeo])
async def get_prospects_geo(session: DBSession):
    stmt = (
        select(Prospect)
        .where(Prospect.latitude.isnot(None), Prospect.longitude.isnot(None))
        .options(selectinload(Prospect.projects))
    )
    result = await session.execute(stmt)
    prospects = result.scalars().all()

    items = []
    for p in prospects:
        status = p.projects[0].status if p.projects else None
        items.append(
            ProspectGeo(
                id=p.id,
                company_name=p.company_name,
                url=p.url,
                latitude=p.latitude,
                longitude=p.longitude,
                industry=p.industry,
                project_status=status,
            )
        )
    return items


@router.get("/{prospect_id}", response_model=ProspectRead)
async def get_prospect(session: DBSession, prospect_id: UUID):
    stmt = select(Prospect).where(Prospect.id == prospect_id).options(selectinload(Prospect.projects))
    result = await session.execute(stmt)
    prospect = result.scalar_one_or_none()
    if not prospect:
        from fastapi import HTTPException
        raise HTTPException(404, "Prospect not found")

    problems = prospect.raw_data.get("site_problems", []) if prospect.raw_data else []
    return ProspectRead(
        id=prospect.id,
        url=prospect.url,
        company_name=prospect.company_name,
        tagline=prospect.tagline,
        contact_emails=prospect.contact_emails or [],
        brand_colors=prospect.brand_colors or [],
        fonts=prospect.fonts or [],
        logo_url=prospect.logo_url,
        social_links=prospect.social_links or {},
        industry=prospect.industry,
        tech_stack=prospect.tech_stack or [],
        raw_data=prospect.raw_data or {},
        latitude=prospect.latitude,
        longitude=prospect.longitude,
        scraped_at=prospect.scraped_at,
        created_at=prospect.created_at,
        project_count=len(prospect.projects),
        site_problems_count=len(problems),
    )


@router.patch("/{prospect_id}", response_model=ProspectRead)
async def update_prospect(session: DBSession, prospect_id: UUID, data: ProspectUpdate):
    prospect = await session.get(Prospect, prospect_id)
    if not prospect:
        from fastapi import HTTPException
        raise HTTPException(404, "Prospect not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prospect, field, value)
    await session.commit()
    await session.refresh(prospect)

    return ProspectRead.model_validate(prospect)
