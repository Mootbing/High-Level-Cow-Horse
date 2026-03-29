"""CEO Agent — top-level orchestrator that receives owner messages via WhatsApp or Dashboard."""

from __future__ import annotations

import json
import uuid

import structlog
from slugify import slugify
from sqlalchemy import select

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent
from openclaw.tools.whatsapp import WHATSAPP_TOOLS, handle_whatsapp_tool
from openclaw.tools.messaging import send_reply, send_media_reply
from openclaw.config import settings
from openclaw.queue.producer import publish

logger = structlog.get_logger()

CEO_SYSTEM_PROMPT = """\
You are the CEO of Clarmi Design Studio, an AI-powered digital design agency.

You receive instructions from the agency owner via the dashboard or WhatsApp. Your job is to:
1. Parse the owner's intent from their message
2. Respond to questions about project status
3. Delegate work to the right team members
4. Report back to the owner with concise updates

Available team members you can delegate to:
- project_manager: For new website projects (breaks down into design -> build -> QA -> deploy)
- inbound: For scraping/researching prospect websites (extracts branding, emails, tech stack)
- outbound: For sending emails via Gmail (cold outreach, project updates)
- designer: For generating design assets (keyframes, videos)
- engineer: For building Next.js websites
- qa: For testing websites
- client_comms: For sending WhatsApp updates to clients

When the owner sends a message, determine the intent:
- "build/create/make a website/landing page for X" -> delegate to project_manager
- "scrape/research/check out X" -> delegate to inbound
- "send email/outreach to X" -> delegate to outbound
- "status/update/what's happening" -> query project status and respond
- "pause/stop/cancel" -> update project status
- General questions -> respond directly

Always respond to the owner. Keep messages concise and professional.
Use the whatsapp_send tool with to="owner" to reply to the owner.

When delegating, use the delegate_task tool with the appropriate target agent and payload.
"""

DELEGATE_TOOL = {
    "name": "delegate_task",
    "description": "Delegate a task to another agent in the organization.",
    "input_schema": {
        "type": "object",
        "properties": {
            "target_agent": {
                "type": "string",
                "enum": [
                    "project_manager",
                    "inbound",
                    "outbound",
                    "designer",
                    "engineer",
                    "qa",
                    "client_comms",
                ],
                "description": "The agent to delegate to.",
            },
            "task_description": {
                "type": "string",
                "description": "What the agent should do.",
            },
            "project_name": {
                "type": "string",
                "description": "Project name if applicable.",
            },
        },
        "required": ["target_agent", "task_description"],
    },
}


@register_agent("ceo")
class CEOAgent(BaseAgent):
    agent_type = "ceo"
    system_prompt = CEO_SYSTEM_PROMPT
    tools = WHATSAPP_TOOLS + [DELEGATE_TOOL]

    def __init__(self):
        super().__init__()
        self._reply_channel = "whatsapp"

    async def process_task(self, message: dict) -> dict:
        """Process incoming messages from WhatsApp, Dashboard, or agent results."""
        msg_type = message.get("type", "")
        self._reply_channel = message.get("reply_channel", "dashboard")

        if msg_type == "dashboard_message":
            prompt = (
                f"Owner sent a message via the dashboard:\n"
                f"Message: {message.get('content')}"
            )
        elif msg_type == "whatsapp_message":
            self._reply_channel = "whatsapp"
            prompt = (
                f"Owner sent a WhatsApp message:\n"
                f"Phone: {message.get('phone')}\n"
                f"Message: {message.get('content')}"
            )
        elif msg_type == "result":
            # Another agent completed a task and is reporting back
            source = message.get("source_agent", "unknown")
            payload = message.get("payload", {})
            result_text = payload.get("result", "")
            original = payload.get("original_prompt", "")
            prompt = (
                f"The {source} agent has completed a task and is reporting results back to you.\n"
                f"Original task: {original}\n\n"
                f"Result:\n{result_text[:4000]}\n\n"
                f"IMPORTANT: This task is ALREADY COMPLETE. Do NOT re-delegate it.\n"
                f"Just summarize the result and send a status update to the owner via whatsapp_send with to='owner'.\n"
                f"Only delegate NEW follow-up work if the result explicitly requires it (e.g., QA failed and needs a fix).\n"
                f"If an email draft was saved, tell the owner it's ready for review in the dashboard."
            )
        else:
            payload = message.get("payload", {})
            prompt = payload.get("prompt", json.dumps(message))

        response = await self.run(prompt)
        return {"status": "completed", "response": response}

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name in ("whatsapp_send", "whatsapp_send_media"):
            to = tool_input.get("to", "")
            is_owner = to == "owner"

            if is_owner and self._reply_channel == "dashboard":
                # Route owner replies through the dashboard
                if tool_name == "whatsapp_send":
                    return await send_reply(
                        message=tool_input["message"],
                        channel="dashboard",
                    )
                else:
                    return await send_media_reply(
                        media_url=tool_input["media_url"],
                        caption=tool_input.get("caption", ""),
                        channel="dashboard",
                    )
            else:
                # Non-owner or WhatsApp channel — use WhatsApp
                return await handle_whatsapp_tool(tool_name, tool_input)
        elif tool_name == "delegate_task":
            target = tool_input["target_agent"]
            project_name = tool_input.get("project_name", "")
            project_id = None

            # Create or fetch Project record so it appears immediately in the dashboard
            if project_name:
                try:
                    project_id = await self._ensure_project(
                        name=project_name,
                        brief=tool_input["task_description"],
                    )
                except Exception as exc:
                    logger.warning(
                        "ensure_project_failed",
                        project_name=project_name,
                        error=str(exc),
                    )

            await self.delegate(
                target_agent=target,
                payload={
                    "prompt": tool_input["task_description"],
                    "project_name": project_name,
                    "project_id": str(project_id) if project_id else None,
                    "source": "ceo",
                },
                project_id=str(project_id) if project_id else None,
            )
            return {"status": "delegated", "to": target, "project_id": str(project_id) if project_id else None}
        return await super().handle_tool_call(tool_name, tool_input)

    async def _ensure_project(self, name: str, brief: str) -> uuid.UUID:
        """Return the id of an existing Project matching *name*, or create one.

        Uses python-slugify to derive a stable slug prefix so repeated
        delegations for the same project reuse the same record.
        If a new project is created, `project_service.create_project` also
        provisions a GitHub repo and Vercel project eagerly.
        """
        from openclaw.db.session import async_session_factory
        from openclaw.models.project import Project
        from openclaw.services.project_service import create_project

        slug_prefix = slugify(name)

        async with async_session_factory() as session:
            # Look for a project whose slug starts with the deterministic prefix.
            # The slug format is "<slugified-name>-<6-hex-chars>" (see project_service).
            stmt = select(Project).where(Project.slug.startswith(slug_prefix))
            result = await session.execute(stmt)
            existing = result.scalars().first()

            if existing:
                logger.info(
                    "project_already_exists",
                    project_id=str(existing.id),
                    slug=existing.slug,
                )
                return existing.id

            # Create project via the service layer — this also provisions
            # the GitHub repo and Vercel project eagerly.
            project = await create_project(
                session=session,
                name=name,
                brief=brief,
            )

            logger.info(
                "project_created",
                project_id=str(project.id),
                slug=project.slug,
                github_repo=project.metadata_.get("github_repo"),
                vercel_project=project.metadata_.get("vercel_project"),
            )
            return project.id
