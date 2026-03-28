"""CEO Agent — top-level orchestrator that receives owner messages via WhatsApp."""

from __future__ import annotations

import json
import structlog

from openclaw.agents.base import BaseAgent
from openclaw.agents.worker import register_agent
from openclaw.tools.whatsapp import WHATSAPP_TOOLS, handle_whatsapp_tool
from openclaw.config import settings
from openclaw.queue.producer import publish

logger = structlog.get_logger()

CEO_SYSTEM_PROMPT = """\
You are the CEO of OpenClaw, an AI-powered digital design agency.

You receive instructions from the agency owner via WhatsApp. Your job is to:
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

Always respond to the owner via WhatsApp. Keep messages concise and professional.
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

    async def process_task(self, message: dict) -> dict:
        """Process incoming WhatsApp messages or delegated tasks."""
        msg_type = message.get("type", "")

        if msg_type == "whatsapp_message":
            prompt = (
                f"Owner sent a WhatsApp message:\n"
                f"Phone: {message.get('phone')}\n"
                f"Message: {message.get('content')}"
            )
        else:
            payload = message.get("payload", {})
            prompt = payload.get("prompt", json.dumps(message))

        response = await self.run(prompt)
        return {"status": "completed", "response": response}

    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> dict:
        if tool_name in ("whatsapp_send", "whatsapp_send_media"):
            return await handle_whatsapp_tool(tool_name, tool_input)
        elif tool_name == "delegate_task":
            target = tool_input["target_agent"]
            await self.delegate(
                target_agent=target,
                payload={
                    "prompt": tool_input["task_description"],
                    "project_name": tool_input.get("project_name", ""),
                    "source": "ceo",
                },
            )
            return {"status": "delegated", "to": target}
        return await super().handle_tool_call(tool_name, tool_input)
