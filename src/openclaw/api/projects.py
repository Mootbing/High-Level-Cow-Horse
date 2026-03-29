"""Projects API endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.db.session import get_session
from openclaw.models.project import Project

router = APIRouter()


@router.get("/projects")
async def list_projects(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(Project).order_by(Project.created_at.desc()).limit(50)
    )
    projects = result.scalars().all()
    return {
        "projects": [
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "status": p.status,
                "deployed_url": p.deployed_url,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    }
