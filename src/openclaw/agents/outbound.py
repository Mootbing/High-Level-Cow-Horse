from __future__ import annotations

import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.registry import register_agent

logger = structlog.get_logger()

OUTBOUND_SYSTEM_PROMPT = """You are the Outbound Agent of OpenClaw, a digital design agency.

Your job is to draft personalized outreach emails. When given prospect data:
1. Craft a personalized email referencing their current branding, tech stack, and design
2. Highlight how OpenClaw can improve their web presence with premium scrolling websites
3. Include relevant examples or portfolio links
4. Keep it concise, professional, and non-spammy
5. Use the gmail_draft tool to save the email as a draft for review
6. The agency owner will review, optionally edit, and approve sending from the dashboard

Always write emails that feel personal, not templated. Reference specific details from their website.
"""

GMAIL_DRAFT_TOOL = {
    "name": "gmail_draft",
    "description": "Save an email as a draft for owner review. The email will NOT be sent immediately — it will appear in the dashboard for approval.",
    "input_schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient email address."},
            "subject": {"type": "string", "description": "Email subject line."},
            "body": {"type": "string", "description": "Email body in HTML format."},
        },
        "required": ["to", "subject", "body"],
    },
}


@register_agent("outbound")
class OutboundAgent(BaseAgent):
    agent_type = "outbound"
    system_prompt = OUTBOUND_SYSTEM_PROMPT
    tools = [GMAIL_DRAFT_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "gmail_draft":
            from openclaw.db.session import async_session_factory
            from openclaw.models.email_log import EmailLog
            from openclaw.tools.messaging import publish_dashboard_event

            # Save as draft — do NOT send via Gmail
            async with async_session_factory() as session:
                log = EmailLog(
                    to_email=tool_input["to"],
                    subject=tool_input["subject"],
                    body=tool_input["body"],
                    status="draft",
                )
                session.add(log)
                await session.commit()
                await session.refresh(log)
                draft_id = str(log.id)

            # Notify dashboard that a new draft is ready for review
            await publish_dashboard_event({
                "type": "email_draft",
                "draft_id": draft_id,
                "to": tool_input["to"],
                "subject": tool_input["subject"],
            })

            logger.info(
                "email_draft_saved",
                draft_id=draft_id,
                to=tool_input["to"],
            )
            return {
                "status": "draft_saved",
                "draft_id": draft_id,
                "to": tool_input["to"],
                "message": "Email saved as draft. Owner will review and approve from the dashboard.",
            }
        return await super().handle_tool_call(tool_name, tool_input)
