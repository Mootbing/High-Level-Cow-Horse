from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.worker import register_agent

logger = structlog.get_logger()

OUTBOUND_SYSTEM_PROMPT = """You are the Outbound Agent of OpenClaw, a digital design agency.

Your job is to send personalized outreach emails via Gmail. When given prospect data:
1. Craft a personalized email referencing their current branding, tech stack, and design
2. Highlight how OpenClaw can improve their web presence with premium scrolling websites
3. Include relevant examples or portfolio links
4. Keep it concise, professional, and non-spammy
5. Use the gmail_send tool to send the email
6. Log the result

Always write emails that feel personal, not templated. Reference specific details from their website.
"""

GMAIL_SEND_TOOL = {
    "name": "gmail_send",
    "description": "Send an email via Gmail.",
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
    tools = [GMAIL_SEND_TOOL]

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name == "gmail_send":
            from openclaw.integrations.gmail_client import send_email
            from openclaw.db.session import async_session_factory
            from openclaw.models.email_log import EmailLog

            result = await send_email(
                to=tool_input["to"],
                subject=tool_input["subject"],
                body=tool_input["body"],
            )

            # Log the email
            async with async_session_factory() as session:
                log = EmailLog(
                    to_email=tool_input["to"],
                    subject=tool_input["subject"],
                    body=tool_input["body"],
                    gmail_message_id=result.get("id", ""),
                )
                session.add(log)
                await session.commit()

            return {"status": "sent", "to": tool_input["to"], "message_id": result.get("id")}
        return await super().handle_tool_call(tool_name, tool_input)
