"""Learning Skill — analyzes completed projects to improve agency
performance over time.

Ported from openclaw.agents.learning.LearningAgent.
"""

from __future__ import annotations

import json
from datetime import date
import structlog

from openclaw.runtime.skill_base import BaseSkill, SkillContext, SkillResult

logger = structlog.get_logger()

LEARNING_SYSTEM_PROMPT = """You are the Learning Agent of Clarmi Design Studio, a digital design agency.

You analyze completed projects to make the agency smarter over time:
1. After each project completes, analyze QA scores, fix loops, and feedback
2. Identify what worked well and what failed
3. Update prompt templates with lessons learned
4. Track improvement metrics over time

Your goal is continuous improvement:
- Increase average Lighthouse scores
- Decrease average fix loops (less QA failures)
- Decrease project completion time
- Incorporate owner preferences into default behavior

When analyzing a project, look for patterns:
- Which components consistently score well?
- Which techniques cause mobile performance issues?
- What design choices does the owner prefer?
- Are there recurring QA failures we can prevent?

Store learnings in the knowledge base and update prompt templates accordingly.
"""

ANALYZE_PROJECT_TOOL = {
    "name": "analyze_project",
    "description": "Analyze a completed project's metrics and history.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_id": {"type": "string"},
        },
        "required": ["project_id"],
    },
}

UPDATE_PROMPT_TOOL = {
    "name": "update_prompt_template",
    "description": "Update a prompt template with new learnings.",
    "input_schema": {
        "type": "object",
        "properties": {
            "template_name": {"type": "string", "description": "e.g., full-site.md, hero-section.md"},
            "new_content": {"type": "string"},
            "reason": {"type": "string", "description": "Why this update was made."},
        },
        "required": ["template_name", "new_content", "reason"],
    },
}

LOG_METRICS_TOOL = {
    "name": "log_metrics",
    "description": "Log daily improvement metrics.",
    "input_schema": {
        "type": "object",
        "properties": {
            "avg_lighthouse": {"type": "number"},
            "avg_fix_loops": {"type": "number"},
            "avg_project_hours": {"type": "number"},
            "total_projects": {"type": "integer"},
            "notes": {"type": "string"},
        },
        "required": [],
    },
}


class LearningSkill(BaseSkill):
    name = "learning"
    description = "Analyzes completed projects to improve agency performance over time"
    tier = "light"
    system_prompt = LEARNING_SYSTEM_PROMPT
    tools = [ANALYZE_PROJECT_TOOL, UPDATE_PROMPT_TOOL, LOG_METRICS_TOOL]
    timeout = 600

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "analyze_project":
            from openclaw.db.session import async_session_factory
            from openclaw.models.project import Project
            from openclaw.models.task import Task
            from sqlalchemy import select
            async with async_session_factory() as session:
                project = await session.get(Project, tool_input["project_id"])
                if not project:
                    return {"error": "Project not found"}
                tasks = await session.execute(
                    select(Task).where(Task.project_id == tool_input["project_id"])
                )
                task_list = tasks.scalars().all()
                return {
                    "project": {"name": project.name, "status": project.status},
                    "tasks": [
                        {"title": t.title, "status": t.status, "agent": t.agent_type,
                         "retry_count": t.retry_count}
                        for t in task_list
                    ],
                }

        elif tool_name == "update_prompt_template":
            from openclaw.db.session import async_session_factory
            from openclaw.models.knowledge import PromptVersion
            from sqlalchemy import select, func
            async with async_session_factory() as session:
                # Get current max version
                result = await session.execute(
                    select(func.max(PromptVersion.version)).where(
                        PromptVersion.template_name == tool_input["template_name"]
                    )
                )
                max_version = result.scalar() or 0
                new_version = PromptVersion(
                    template_name=tool_input["template_name"],
                    version=max_version + 1,
                    content=tool_input["new_content"],
                    reason=tool_input["reason"],
                )
                session.add(new_version)
                await session.commit()

                # Also write to disk
                import os
                prompt_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates", "prompts")
                prompt_dir = os.path.normpath(prompt_dir)
                os.makedirs(prompt_dir, exist_ok=True)
                filepath = os.path.join(prompt_dir, tool_input["template_name"])
                with open(filepath, "w") as f:
                    f.write(tool_input["new_content"])

                return {"status": "updated", "version": max_version + 1}

        elif tool_name == "log_metrics":
            from openclaw.db.session import async_session_factory
            from openclaw.models.knowledge import ImprovementMetric
            async with async_session_factory() as session:
                metric = ImprovementMetric(
                    metric_date=date.today(),
                    avg_lighthouse=tool_input.get("avg_lighthouse"),
                    avg_fix_loops=tool_input.get("avg_fix_loops"),
                    avg_project_hours=tool_input.get("avg_project_hours"),
                    total_projects=tool_input.get("total_projects"),
                    notes=tool_input.get("notes"),
                )
                session.add(metric)
                await session.commit()
                return {"status": "logged", "date": str(date.today())}

        return await super().handle_tool_call(tool_name, tool_input)
