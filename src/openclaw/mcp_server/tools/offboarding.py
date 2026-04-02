"""Client offboarding tool — delete project from GitHub, Vercel, and database."""

import json
import shutil

import structlog

from openclaw.mcp_server.server import mcp

logger = structlog.get_logger()


@mcp.tool()
async def offboard_client(project_name: str, confirm: bool = False) -> str:
    """Permanently delete a client project from GitHub, Vercel, and the database.

    Removes: GitHub repo, Vercel project (takes site offline), and all database
    records (project, prospect, tasks, assets, deployments, messages, email logs,
    agent logs, knowledge entries).

    This is irreversible. Use for client offboarding.

    Two-step process:
    1. Call with confirm=False (default) to preview what will be deleted.
    2. Call again with confirm=True and the exact project name to execute.

    Args:
        project_name: Exact project name to offboard.
        confirm: Must be True to actually delete. Defaults to False (preview only).
    """
    from sqlalchemy import delete, func, select

    from openclaw.db.session import async_session_factory
    from openclaw.integrations.github_client import delete_repo
    from openclaw.integrations.vercel_client import delete_project as delete_vercel
    from openclaw.models.agent_log import AgentLog
    from openclaw.models.asset import Asset
    from openclaw.models.deployment import Deployment
    from openclaw.models.email_log import EmailLog
    from openclaw.models.knowledge import KnowledgeBase
    from openclaw.models.message import Message
    from openclaw.models.project import Project
    from openclaw.models.prospect import Prospect
    from openclaw.models.task import Task

    async with async_session_factory() as session:
        # Exact match first
        stmt = select(Project).where(Project.name == project_name)
        result = await session.execute(stmt)
        project = result.scalar_one_or_none()

        # If no exact match, search for candidates but never auto-delete
        if not project:
            stmt = select(Project.name, Project.slug, Project.status, Project.deployed_url).where(
                Project.name.ilike(f"%{project_name}%")
            )
            result = await session.execute(stmt)
            candidates = result.all()

            if not candidates:
                return json.dumps({"status": "error", "message": f"No project matching '{project_name}' found."})

            return json.dumps({
                "status": "disambiguation",
                "message": f"No exact match for '{project_name}'. Did you mean one of these? Call again with the exact name.",
                "candidates": [
                    {"name": c.name, "slug": c.slug, "status": c.status, "deployed_url": c.deployed_url}
                    for c in candidates
                ],
            }, indent=2)

        project_id = project.id
        prospect_id = project.prospect_id
        metadata = project.metadata_ or {}
        github_repo = metadata.get("github_repo")
        vercel_project = metadata.get("vercel_project")

        # --- Preview mode (confirm=False) ---
        if not confirm:
            # Count related records
            child_tables = [
                ("email_logs", EmailLog, EmailLog.project_id),
                ("agent_logs", AgentLog, AgentLog.project_id),
                ("messages", Message, Message.project_id),
                ("deployments", Deployment, Deployment.project_id),
                ("assets", Asset, Asset.project_id),
                ("tasks", Task, Task.project_id),
                ("knowledge_entries", KnowledgeBase, KnowledgeBase.project_id),
            ]
            record_counts = {}
            for label, model, fk_col in child_tables:
                count = await session.scalar(
                    select(func.count()).select_from(model).where(fk_col == project_id)
                )
                if count:
                    record_counts[label] = count

            return json.dumps({
                "status": "preview",
                "message": "This will PERMANENTLY delete the following. Call again with confirm=True to proceed.",
                "project": project.name,
                "slug": project.slug,
                "deployed_url": project.deployed_url,
                "will_delete": {
                    "github_repo": github_repo,
                    "vercel_project": vercel_project,
                    "database_records": record_counts,
                },
            }, indent=2)

        logger.info("offboarding_client", project=project.name, slug=project.slug)

        results = {
            "github": None,
            "vercel": None,
            "database": {},
        }

        # --- Delete GitHub repo ---
        if github_repo:
            try:
                ok = await delete_repo(github_repo)
                results["github"] = "deleted" if ok else "failed"
            except Exception as exc:
                results["github"] = f"error: {str(exc)[:200]}"
                logger.error("offboard_github_error", error=str(exc))
        else:
            results["github"] = "skipped (no repo)"

        # --- Delete Vercel project ---
        if vercel_project:
            try:
                ok = await delete_vercel(vercel_project)
                results["vercel"] = "deleted" if ok else "failed"
            except Exception as exc:
                results["vercel"] = f"error: {str(exc)[:200]}"
                logger.error("offboard_vercel_error", error=str(exc))
        else:
            results["vercel"] = "skipped (no project)"

        # --- Delete database records (child tables first) ---
        child_tables = [
            ("email_logs", EmailLog, EmailLog.project_id),
            ("agent_logs", AgentLog, AgentLog.project_id),
            ("messages", Message, Message.project_id),
            ("deployments", Deployment, Deployment.project_id),
            ("assets", Asset, Asset.project_id),
            ("tasks", Task, Task.project_id),
            ("knowledge_entries", KnowledgeBase, KnowledgeBase.project_id),
        ]

        for label, model, fk_col in child_tables:
            stmt = delete(model).where(fk_col == project_id)
            res = await session.execute(stmt)
            results["database"][label] = res.rowcount

        # Delete prospect email logs (linked to prospect, not project)
        if prospect_id:
            stmt = delete(EmailLog).where(EmailLog.prospect_id == prospect_id)
            res = await session.execute(stmt)
            results["database"]["prospect_email_logs"] = res.rowcount

        # Delete the project itself
        await session.execute(delete(Project).where(Project.id == project_id))
        results["database"]["project"] = 1

        # Delete the prospect (only if no other projects reference it)
        if prospect_id:
            other = await session.scalar(
                select(Project.id).where(
                    Project.prospect_id == prospect_id,
                    Project.id != project_id,
                ).limit(1)
            )
            if other is None:
                await session.execute(delete(Prospect).where(Prospect.id == prospect_id))
                results["database"]["prospect"] = 1
            else:
                results["database"]["prospect"] = "skipped (shared with other projects)"

        await session.commit()

        # --- Clean up local project files ---
        from openclaw.config import settings

        local_dir = f"{settings.STORAGE_PATH}/{project.slug}"
        try:
            shutil.rmtree(local_dir, ignore_errors=True)
            results["local_files"] = "cleaned"
        except Exception:
            results["local_files"] = "skipped"

    logger.info("offboarding_complete", project=project_name, results=results)

    return json.dumps({
        "status": "ok",
        "project": project.name,
        "slug": project.slug,
        "results": results,
    }, indent=2)
