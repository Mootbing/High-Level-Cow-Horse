"""Deployment API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from openclaw.db.deps import DBSession
from openclaw.models.deployment import Deployment
from openclaw.api.schemas.deployments import DeploymentRead

router = APIRouter(tags=["deployments"])


@router.get("/projects/{project_id}/deployments", response_model=list[DeploymentRead])
async def list_project_deployments(session: DBSession, project_id: UUID):
    stmt = (
        select(Deployment)
        .where(Deployment.project_id == project_id)
        .order_by(Deployment.created_at.desc())
    )
    result = await session.execute(stmt)
    return [DeploymentRead.model_validate(d) for d in result.scalars().all()]
