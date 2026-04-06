from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from openclaw.models.deployment import Deployment
from openclaw.integrations.vercel_client import trigger_deployment, get_deployment_status

logger = structlog.get_logger()


async def deploy_project(session: AsyncSession, project_id: str, project_name: str, files: list[dict]) -> Deployment:
    """Deploy a project to Vercel and track the deployment."""
    result = await trigger_deployment(project_name, files)
    deployment = Deployment(
        project_id=project_id,
        vercel_deployment_id=result.get("id", ""),
        url=result.get("url", ""),
        status="building",
    )
    session.add(deployment)
    await session.commit()
    await session.refresh(deployment)
    return deployment


async def check_deployment(session: AsyncSession, vercel_deployment_id: str) -> str:
    """Check and update deployment status."""
    deployment = await session.get(Deployment, vercel_deployment_id)
    if not deployment or not deployment.vercel_deployment_id:
        return "unknown"
    status_data = await get_deployment_status(deployment.vercel_deployment_id)
    new_status = status_data.get("readyState", "unknown")
    if new_status == "READY":
        deployment.status = "ready"
    elif new_status == "ERROR":
        deployment.status = "error"
    await session.commit()
    return deployment.status
