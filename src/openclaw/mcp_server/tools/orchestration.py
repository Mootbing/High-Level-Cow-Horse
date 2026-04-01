"""Orchestration tools — superprompt management and parallel build coordination."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import structlog

from openclaw.config import settings
from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()


def _storage_dir(project_name: str) -> str:
    """Project storage directory (parent of /site)."""
    safe_name = os.path.basename(project_name.replace("..", "").strip("/")) or "unnamed"
    return os.path.join(settings.STORAGE_PATH, safe_name)


def _project_dir(project_name: str) -> str:
    """Project site directory (for code files)."""
    return os.path.join(_storage_dir(project_name), "site")


async def _resolve_project(project_name: str):
    """Find the Project record by name/slug. Returns (project, session) or raises."""
    from openclaw.db.session import async_session_factory
    from openclaw.models.project import Project
    from slugify import slugify
    from sqlalchemy import select

    session = async_session_factory()
    async with session:
        slug_prefix = slugify(project_name)
        stmt = select(Project).where(Project.slug.startswith(slug_prefix))
        result = await session.execute(stmt)
        project = result.scalars().first()

        if not project:
            stmt = select(Project).where(Project.name.ilike(f"%{project_name}%")).limit(1)
            result = await session.execute(stmt)
            project = result.scalars().first()

        return project, session


# ──────────────────────────────────────────────────────────────────────────────
# Superprompt Management
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def store_superprompt(
    project_name: str,
    superprompt: str,
    section_plan: str,
) -> str:
    """Store the build superprompt and section plan for orchestrated parallel builds.

    The superprompt is the comprehensive context document that all section sub-agents
    receive. It contains brand identity, site structure, generated assets, design
    decisions, tech rules, and per-section briefs.

    section_plan is a JSON array defining the parallel work:
    [
      {"section_id": "hero", "component_files": ["components/Hero.tsx"], "priority": 1, "description": "..."},
      {"section_id": "features", "component_files": ["components/Features.tsx"], "priority": 2, "description": "..."}
    ]

    Writes superprompt.md to the project directory and stores section_plan in
    project metadata for build status tracking.
    """
    try:
        plan_obj = json.loads(section_plan)
    except json.JSONDecodeError as e:
        return json.dumps({"status": "error", "message": f"Invalid section_plan JSON: {e}"})

    # Write superprompt to filesystem
    site_dir = _project_dir(project_name)
    os.makedirs(site_dir, exist_ok=True)
    superprompt_path = os.path.join(site_dir, "superprompt.md")
    with open(superprompt_path, "w") as f:
        f.write(superprompt)

    # Store section plan in project metadata
    try:
        from openclaw.db.session import async_session_factory
        from openclaw.models.project import Project
        from slugify import slugify
        from sqlalchemy import select

        async with async_session_factory() as session:
            slug_prefix = slugify(project_name)
            stmt = select(Project).where(Project.slug.startswith(slug_prefix))
            result = await session.execute(stmt)
            project = result.scalars().first()

            if not project:
                stmt = select(Project).where(Project.name.ilike(f"%{project_name}%")).limit(1)
                result = await session.execute(stmt)
                project = result.scalars().first()

            if project:
                existing = project.metadata_ or {}
                project.metadata_ = {
                    **existing,
                    "section_plan": plan_obj,
                    "superprompt_path": superprompt_path,
                    "build_started_at": datetime.now(timezone.utc).isoformat(),
                }
                await session.commit()

                # Create parent build task
                from openclaw.services.task_service import create_task
                parent_task = await create_task(
                    session,
                    project_id=str(project.id),
                    agent_type="orchestrator",
                    title=f"Build {project_name} website",
                    input_data={"section_plan": plan_obj},
                )

                # Create sub-tasks for each section
                sub_task_ids = []
                for section in plan_obj:
                    sub_task = await create_task(
                        session,
                        project_id=str(project.id),
                        agent_type="section_builder",
                        title=f"Build {section['section_id']} section",
                        parent_task_id=str(parent_task.id),
                        priority=section.get("priority", 5),
                        input_data={
                            "section_id": section["section_id"],
                            "component_files": section["component_files"],
                            "description": section.get("description", ""),
                        },
                    )
                    sub_task_ids.append(str(sub_task.id))

                logger.info(
                    "superprompt_stored",
                    project=project_name,
                    sections=len(plan_obj),
                    parent_task=str(parent_task.id),
                )

                return json.dumps({
                    "status": "stored",
                    "superprompt_path": superprompt_path,
                    "sections": len(plan_obj),
                    "parent_task_id": str(parent_task.id),
                    "sub_task_ids": sub_task_ids,
                })

    except Exception as exc:
        logger.warning("superprompt_db_failed", error=str(exc)[:300])

    return json.dumps({
        "status": "stored_filesystem_only",
        "superprompt_path": superprompt_path,
        "sections": len(plan_obj),
        "note": "Stored on filesystem. Database task creation failed — poll via filesystem instead.",
    })


@mcp.tool()
async def get_superprompt(project_name: str) -> str:
    """Read the superprompt for a project. Used by sub-agents to get full build context.

    Returns the superprompt markdown content and the section plan.
    """
    site_dir = _project_dir(project_name)
    superprompt_path = os.path.join(site_dir, "superprompt.md")

    if not os.path.isfile(superprompt_path):
        return json.dumps({"status": "error", "message": "No superprompt found. Run store_superprompt first."})

    with open(superprompt_path, "r") as f:
        content = f.read()

    # Also load section plan from project metadata
    section_plan = None
    try:
        from openclaw.db.session import async_session_factory
        from openclaw.models.project import Project
        from slugify import slugify
        from sqlalchemy import select

        async with async_session_factory() as session:
            slug_prefix = slugify(project_name)
            stmt = select(Project).where(Project.slug.startswith(slug_prefix))
            result = await session.execute(stmt)
            project = result.scalars().first()
            if project and project.metadata_:
                section_plan = project.metadata_.get("section_plan")
    except Exception:
        pass

    return json.dumps({
        "status": "ok",
        "superprompt": content,
        "section_plan": section_plan,
        "superprompt_length": len(content),
    })


# ──────────────────────────────────────────────────────────────────────────────
# Build Status Tracking
# ──────────────────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_build_status(project_name: str) -> str:
    """Check the completion status of all section build sub-tasks.

    Returns per-section status and whether all sections are done.
    The orchestrator polls this after spawning sub-agents to know when
    assembly can begin.
    """
    try:
        from openclaw.db.session import async_session_factory
        from openclaw.models.project import Project
        from openclaw.models.task import Task
        from slugify import slugify
        from sqlalchemy import select

        async with async_session_factory() as session:
            # Find project
            slug_prefix = slugify(project_name)
            stmt = select(Project).where(Project.slug.startswith(slug_prefix))
            result = await session.execute(stmt)
            project = result.scalars().first()

            if not project:
                return json.dumps({"status": "error", "message": "Project not found"})

            # Find the orchestrator parent task (most recent)
            stmt = (
                select(Task)
                .where(Task.project_id == project.id)
                .where(Task.agent_type == "orchestrator")
                .order_by(Task.created_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            parent_task = result.scalars().first()

            if not parent_task:
                return json.dumps({"status": "error", "message": "No build task found. Run store_superprompt first."})

            # Get all section sub-tasks
            stmt = (
                select(Task)
                .where(Task.parent_task_id == parent_task.id)
                .order_by(Task.priority)
            )
            result = await session.execute(stmt)
            sub_tasks = list(result.scalars().all())

            sections = []
            for t in sub_tasks:
                section_data = {
                    "task_id": str(t.id),
                    "section_id": t.input_data.get("section_id", ""),
                    "component_files": t.input_data.get("component_files", []),
                    "status": t.status,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "error": t.error,
                }
                sections.append(section_data)

            completed = sum(1 for s in sections if s["status"] == "completed")
            failed = sum(1 for s in sections if s["status"] == "failed")
            total = len(sections)
            all_done = completed + failed == total and total > 0

            return json.dumps({
                "status": "ok",
                "parent_task_id": str(parent_task.id),
                "total_sections": total,
                "completed": completed,
                "failed": failed,
                "in_progress": total - completed - failed,
                "all_done": all_done,
                "sections": sections,
            })

    except Exception as exc:
        logger.warning("get_build_status_failed", error=str(exc)[:300])
        return json.dumps({"status": "error", "message": str(exc)[:200]})


@mcp.tool()
async def mark_section_complete(
    project_name: str,
    section_id: str,
    component_files: list[str],
    status: str = "completed",
    error: str | None = None,
) -> str:
    """Mark a section build task as completed (or failed).

    Called by sub-agents after writing their component file(s).
    Updates the Task record's status, output_data, and timestamps.

    status: "completed" (success) or "failed" (with error message)
    """
    try:
        from openclaw.db.session import async_session_factory
        from openclaw.models.project import Project
        from openclaw.models.task import Task
        from openclaw.services.task_service import update_task_status
        from slugify import slugify
        from sqlalchemy import select

        async with async_session_factory() as session:
            # Find project
            slug_prefix = slugify(project_name)
            stmt = select(Project).where(Project.slug.startswith(slug_prefix))
            result = await session.execute(stmt)
            project = result.scalars().first()

            if not project:
                return json.dumps({"status": "error", "message": "Project not found"})

            # Find the section task by section_id in input_data
            # First find parent orchestrator task
            stmt = (
                select(Task)
                .where(Task.project_id == project.id)
                .where(Task.agent_type == "orchestrator")
                .order_by(Task.created_at.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            parent_task = result.scalars().first()

            if not parent_task:
                return json.dumps({"status": "error", "message": "No orchestrator task found"})

            # Find the specific section sub-task
            stmt = (
                select(Task)
                .where(Task.parent_task_id == parent_task.id)
                .where(Task.agent_type == "section_builder")
            )
            result = await session.execute(stmt)
            sub_tasks = list(result.scalars().all())

            target_task = None
            for t in sub_tasks:
                if t.input_data.get("section_id") == section_id:
                    target_task = t
                    break

            if not target_task:
                return json.dumps({
                    "status": "error",
                    "message": f"No sub-task found for section '{section_id}'",
                })

            # Verify component files exist on disk
            site_dir = _project_dir(project_name)
            files_verified = []
            for fp in component_files:
                full_path = os.path.join(site_dir, fp)
                exists = os.path.isfile(full_path)
                files_verified.append({"path": fp, "exists": exists})

            # Update task
            output_data = {
                "component_files": component_files,
                "files_verified": files_verified,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }

            updated = await update_task_status(
                session,
                task_id=str(target_task.id),
                status=status,
                output_data=output_data,
                error=error,
            )

            logger.info(
                "section_marked",
                project=project_name,
                section=section_id,
                status=status,
                files=len(component_files),
            )

            return json.dumps({
                "status": "updated",
                "section_id": section_id,
                "task_status": status,
                "files_verified": files_verified,
            })

    except Exception as exc:
        logger.warning("mark_section_failed", error=str(exc)[:300])
        return json.dumps({"status": "error", "message": str(exc)[:200]})
