"""Project management tools — create, list, update projects with GitHub + Vercel provisioning."""

import json

from openclaw.mcp_server.server import mcp


@mcp.tool()
async def create_project(name: str, brief: str, client_phone: str | None = None) -> str:
    """Create a new project with automatic GitHub repo + Vercel project provisioning.

    Returns project ID, slug, GitHub URL, and Vercel project name.
    Use this at the start of a website build pipeline.
    """
    from openclaw.db.session import async_session_factory
    from openclaw.services.project_service import create_project as _create

    async with async_session_factory() as session:
        project = await _create(
            session=session,
            name=name,
            brief=brief,
            client_phone=client_phone,
        )
        metadata = project.metadata_ or {}
        return json.dumps({
            "project_id": str(project.id),
            "name": project.name,
            "slug": project.slug,
            "status": project.status,
            "github_repo": metadata.get("github_repo"),
            "github_url": metadata.get("github_url"),
            "vercel_project": metadata.get("vercel_project"),
        })


@mcp.tool()
async def get_project_status(project_name: str | None = None) -> str:
    """Get status of all projects (or filter by name). Returns projects, task counts, and recent activity."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.project import Project
    from openclaw.models.task import Task
    from sqlalchemy import select, func

    async with async_session_factory() as session:
        stmt = select(Project).order_by(Project.created_at.desc()).limit(10)
        if project_name:
            stmt = select(Project).where(
                Project.name.ilike(f"%{project_name}%")
            ).limit(5)
        result = await session.execute(stmt)
        projects = result.scalars().all()

        summaries = []
        for p in projects:
            task_counts = {}
            for status in ["pending", "in_progress", "completed", "failed"]:
                count = await session.scalar(
                    select(func.count()).select_from(Task).where(
                        Task.project_id == p.id, Task.status == status
                    )
                )
                if count:
                    task_counts[status] = count

            summaries.append({
                "project_id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "status": p.status,
                "deployed_url": p.deployed_url,
                "github": (p.metadata_ or {}).get("github_url"),
                "tasks": task_counts or "no tasks yet",
                "created": p.created_at.isoformat() if p.created_at else None,
            })

        return json.dumps({"projects": summaries, "total": len(summaries)}, indent=2)


@mcp.tool()
async def update_project_status(project_id: str, status: str) -> str:
    """Update a project's pipeline status. Valid statuses: intake, design, build, qa, deployed."""
    import uuid as _uuid
    from openclaw.db.session import async_session_factory
    from openclaw.services.project_service import update_project_status as _update

    try:
        _uuid.UUID(project_id)
    except ValueError:
        return json.dumps({"error": f"Invalid project_id: {project_id}"})

    async with async_session_factory() as session:
        project = await _update(session=session, project_id=project_id, status=status)
        if project:
            return json.dumps({"project_id": str(project.id), "status": project.status})
        return json.dumps({"error": f"Project {project_id} not found"})


@mcp.tool()
async def list_projects(status: str | None = None) -> str:
    """List all projects, optionally filtered by status (intake, design, build, qa, deployed)."""
    from openclaw.db.session import async_session_factory
    from openclaw.services.project_service import list_projects as _list

    async with async_session_factory() as session:
        projects = await _list(session=session, status=status)
        return json.dumps([
            {
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "status": p.status,
                "deployed_url": p.deployed_url,
                "created": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ], indent=2)
